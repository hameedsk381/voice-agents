"""
Latency benchmark for the Voise AI voice pipeline.

Measures p50/p95/p99 latency for STT (mock + Deepgram) and LLM (Groq)
via direct API calls. Results printed to stdout and optionally saved
to a JSON report.

Usage:
    python scripts/bench_latency.py --iterations 10 --output report.json
"""

import argparse
import asyncio
import json
import math
import os
import sys
import time
from dataclasses import dataclass, field
from statistics import stdev
from typing import Dict, List, Optional


# Ensure backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("STT_PROVIDER", "mock")


def percentile(data: List[float], p: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    return s[int(k)] if f == c else s[f] * (c - k) + s[c] * (k - f)


@dataclass
class BenchResult:
    label: str
    samples: List[float] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def record(self, elapsed_ms: float) -> None:
        self.samples.append(elapsed_ms)

    def report(self) -> Dict:
        if not self.samples:
            return {"label": self.label, "n": 0, "error": "no samples"}
        n = len(self.samples)
        return {
            "label": self.label,
            "n": n,
            "min_ms": round(min(self.samples), 2),
            "p50_ms": round(percentile(self.samples, 50), 2),
            "p95_ms": round(percentile(self.samples, 95), 2),
            "p99_ms": round(percentile(self.samples, 99), 2),
            "max_ms": round(max(self.samples), 2),
            "mean_ms": round(sum(self.samples) / n, 2),
            "stdev_ms": round(stdev(self.samples), 2) if n > 1 else 0.0,
            "metadata": self.metadata,
        }

    def print_report(self) -> None:
        r = self.report()
        if "error" in r:
            print(f"  [skip] {self.label}: {r['error']}")
            return
        print(f"  [OK] {self.label}  (n={r['n']})")
        print(f"       min={r['min_ms']}ms  p50={r['p50_ms']}ms  p95={r['p95_ms']}ms  p99={r['p99_ms']}ms  max={r['max_ms']}ms")
        print(f"       mean={r['mean_ms']}ms  stdev={r['stdev_ms']}ms")
        if r.get("metadata"):
            for k, v in r["metadata"].items():
                print(f"       {k}={v}")


# ─── Benchmarks ──────────────────────────────────────────────────────


async def bench_mock_stt(iterations: int) -> BenchResult:
    from app.services.stt.mock_provider import MockSTT
    br = BenchResult(label="Mock STT (simulated 50ms)")
    stt = MockSTT()
    audio = b"0" * 16000
    for _ in range(iterations):
        t0 = time.perf_counter()
        await stt.transcribe(audio, language="hi")
        br.record((time.perf_counter() - t0) * 1000)
    return br


async def bench_deepgram(iterations: int) -> BenchResult:
    br = BenchResult(label="Deepgram STT (nova-2, en-IN)")
    api_key = os.getenv("DEEPGRAM_API_KEY", "")
    if not api_key or api_key == "your-deepgram-api-key":
        br.metadata["skipped"] = "DEEPGRAM_API_KEY not set in .env"
        return br
    audio = b"0" * 16000
    import httpx
    for i in range(iterations):
        t0 = time.perf_counter()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.deepgram.com/v1/listen?language=en&model=nova-2",
                headers={"Authorization": f"Token {api_key}"},
                content=audio,
            )
            resp.raise_for_status()
        br.record((time.perf_counter() - t0) * 1000)
        if i > 0 and i % 5 == 0:
            print(f"    deepgram: {i}/{iterations}")
    return br


async def bench_groq(
    model: str, prompt: str, iterations: int, max_tokens: int = 50
) -> BenchResult:
    br = BenchResult(label=f"Groq {model}")
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "your-groq-api-key":
        br.metadata["skipped"] = "GROQ_API_KEY not set in .env"
        return br
    br.metadata["model"] = model
    br.metadata["max_tokens"] = max_tokens
    br.metadata["prompt_len"] = len(prompt)

    import httpx
    for i in range(iterations):
        t0 = time.perf_counter()
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
        br.record((time.perf_counter() - t0) * 1000)
        if i > 0 and i % 5 == 0:
            print(f"    {model}: {i}/{iterations}")
    return br


async def bench_pipeline(iterations: int) -> BenchResult:
    br = BenchResult(label="STT + LLM (mock+groq-70b)")
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key or groq_key == "your-groq-api-key":
        br.metadata["skipped"] = "GROQ_API_KEY not set in .env"
        return br
    from app.services.stt.mock_provider import MockSTT
    stt = MockSTT()
    audio = b"0" * 16000
    import httpx
    for i in range(iterations):
        t0 = time.perf_counter()
        result = await stt.transcribe(audio, language="en")
        text = result.text
        t1 = time.perf_counter()
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": f"Answer briefly: {text}"}],
                    "max_tokens": 30,
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
        t2 = time.perf_counter()
        br.record((t2 - t0) * 1000)
        stt_ms = (t1 - t0) * 1000
        llm_ms = (t2 - t1) * 1000
        prev = br.metadata
        br.metadata = {
            "avg_stt_ms": round((prev.get("avg_stt_ms", 0) * i + stt_ms) / (i + 1), 2),
            "avg_llm_ms": round((prev.get("avg_llm_ms", 0) * i + llm_ms) / (i + 1), 2),
        }
        if i > 0 and i % 5 == 0:
            print(f"    pipeline: {i}/{iterations}")
    return br


# ─── Runner ──────────────────────────────────────────────────────────


async def run_all(iterations: int = 10, output: Optional[str] = None) -> List[Dict]:
    print(f"\n{'='*60}")
    print(f"  Voise AI -- Pipeline Latency Benchmark")
    print(f"  Iterations per test: {iterations}")
    print(f"{'='*60}\n")

    results = []

    print("[1/5] Mock STT ...")
    r = await bench_mock_stt(iterations)
    r.print_report()
    results.append(r.report())

    print("\n[2/5] Deepgram STT ...")
    r = await bench_deepgram(min(iterations, 5))
    r.print_report()
    results.append(r.report())

    print("\n[3/5] Groq LLM (70B, short prompt) ...")
    r = await bench_groq("llama-3.3-70b-versatile",
                         "What is the capital of France?", iterations)
    r.print_report()
    results.append(r.report())

    print("\n[4/5] Groq LLM (8B, short prompt) ...")
    r = await bench_groq("llama-3.1-8b-instant",
                         "What is the capital of France?", iterations)
    r.print_report()
    results.append(r.report())

    print("\n[5/5] Full pipeline (mock STT + Groq 70B) ...")
    r = await bench_pipeline(min(iterations, 10))
    r.print_report()
    results.append(r.report())

    print(f"\n{'='*60}")
    print("  Benchmark complete")
    print(f"{'='*60}\n")

    if output:
        with open(output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"  Report saved to: {output}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Voice pipeline latency benchmark")
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    results = asyncio.run(run_all(args.iterations, args.output))

    tested = [r for r in results if "error" not in r and r.get("n", 0) > 0]
    print(f"  Benchmarks run: {len(tested)}/{len(results)}")
    avg = sum(r.get("mean_ms", 0) for r in tested)
    if tested:
        print(f"  Aggregate mean: {round(avg / len(tested), 2)}ms across stages\n")


if __name__ == "__main__":
    main()
