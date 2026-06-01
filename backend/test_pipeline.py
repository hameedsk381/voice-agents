"""Test WS without token (dev mode bypass)."""
import asyncio, json, base64, httpx, websockets

async def run():
    aid = "45705f3a-87f6-45fd-82a9-d61779058d0d"

    # Test 1: no token → should work in dev
    async with websockets.connect(f"ws://localhost:8001/api/v1/orchestrator/ws/{aid}?language=hi") as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=30)
        d = json.loads(msg)
        assert d["type"] == "session_start"
        print(f"WS no-token: {d['type']} session={d.get('session_id')[:12]}...")

        # Send audio chunks
        key = "sk_tls2dfit_AILktu9PuvlGoPtMpS4DMhjd"
        async with httpx.AsyncClient(timeout=30.0) as hc:
            r = await hc.post("https://api.sarvam.ai/text-to-speech", json={
                "text": "namaste duniya", "target_language_code": "hi-IN",
                "speaker": "shubh", "model": "bulbul:v3",
                "output_audio_codec": "wav", "speech_sample_rate": "24000",
            }, headers={"api-subscription-key": key, "Content-Type": "application/json"})
            wav_bytes = base64.b64decode(r.json()["audios"][0])

        chunk_size = 4800
        chunks = [wav_bytes[i:i+chunk_size] for i in range(0, len(wav_bytes), chunk_size)]
        for chunk in chunks:
            await ws.send(json.dumps({"type": "audio", "audio": base64.b64encode(chunk).decode("utf-8")}))
            await asyncio.sleep(0.05)

        had_audio = False
        while True:
            msg = await asyncio.wait_for(ws.recv(), timeout=20)
            d = json.loads(msg)
            t = d["type"]
            if t == "audio":
                print(f"  Audio: {len(d.get('data', ''))} chars")
                had_audio = True
            elif t == "text_chunk":
                print(f"  Text: {d.get('text', '')[:60]}")
            elif t == "turn_metrics":
                print(f"  STT: {d.get('stt_ms', 0):.0f}ms TTS: {d.get('tts_ms', 0):.0f}ms")
            elif t == "end_response":
                break
            elif t == "error":
                print(f"  ERROR: {d.get('message')}")
                break
        assert had_audio, "No audio!"
        print("PASS: No-token WS auth bypass + full pipeline works")
        await ws.close()

if __name__ == "__main__":
    asyncio.run(run())
