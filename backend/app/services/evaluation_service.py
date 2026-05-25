import time
import json
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable, Awaitable
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from loguru import logger

from app.models.analytics import EvalRun, EvalTestCaseResult, TraceLog


class EvaluationService:
    def __init__(self, db: Session):
        self.db = db

    async def create_run(
        self,
        suite_name: str,
        model_under_test: str,
        run_metadata: Optional[Dict[str, Any]] = None,
    ) -> EvalRun:
        run = EvalRun(
            id=str(uuid.uuid4()),
            suite_name=suite_name,
            status="running",
            model_under_test=model_under_test,
            run_metadata=run_metadata or {},
        )
        self.db.add(run)
        self.db.commit()
        return run

    async def complete_run(self, run_id: str):
        run = self.db.query(EvalRun).filter(EvalRun.id == run_id).first()
        if not run:
            return
        run.status = "completed"
        run.completed_at = datetime.utcnow()
        total = run.total_tests or 1
        run.score = round((run.passed / total) * 100, 2) if total > 0 else 0
        self.db.commit()

    async def record_test_result(
        self,
        run_id: str,
        test_name: str,
        input_text: str,
        expected_output: Optional[str],
        actual_output: Optional[str],
        passed: bool,
        score: Optional[float] = None,
        latency_ms: Optional[float] = None,
        failure_reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> EvalTestCaseResult:
        result = EvalTestCaseResult(
            id=str(uuid.uuid4()),
            run_id=run_id,
            test_name=test_name,
            input_text=input_text,
            expected_output=expected_output,
            actual_output=actual_output,
            passed=passed,
            score=score,
            latency_ms=latency_ms,
            failure_reason=failure_reason,
            details=details or {},
        )
        self.db.add(result)

        run = self.db.query(EvalRun).filter(EvalRun.id == run_id).first()
        if run:
            run.total_tests = (run.total_tests or 0) + 1
            if passed:
                run.passed = (run.passed or 0) + 1
            else:
                run.failed = (run.failed or 0) + 1
        self.db.commit()
        return result

    async def run_golden_suite(
        self,
        suite_name: str,
        model_under_test: str,
        test_cases: List[Dict[str, Any]],
        inference_fn: Callable[[str, str], Awaitable[str]],
    ) -> EvalRun:
        run = await self.create_run(suite_name, model_under_test)

        for tc in test_cases:
            input_text = tc.get("input", "")
            expected = tc.get("expected", tc.get("expected_output"))
            system_prompt = tc.get("system_prompt", "You are a helpful assistant.")
            start = time.perf_counter()
            try:
                actual = await inference_fn(input_text, system_prompt)
                elapsed = (time.perf_counter() - start) * 1000
                passed = tc.get("evaluator", self._default_evaluator)(actual, expected)
                await self.record_test_result(
                    run_id=run.id,
                    test_name=tc.get("name", input_text[:50]),
                    input_text=input_text,
                    expected_output=expected,
                    actual_output=actual,
                    passed=passed,
                    latency_ms=round(elapsed, 2),
                )
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                await self.record_test_result(
                    run_id=run.id,
                    test_name=tc.get("name", input_text[:50]),
                    input_text=input_text,
                    expected_output=expected,
                    actual_output=None,
                    passed=False,
                    latency_ms=round(elapsed, 2),
                    failure_reason=str(e),
                )

        await self.complete_run(run.id)
        return run

    def _default_evaluator(self, actual: Optional[str], expected: Optional[str]) -> bool:
        if expected is None:
            return actual is not None and len(actual) > 0
        if actual is None:
            return False
        return expected.lower().strip() in actual.lower().strip()

    async def get_run_summary(self, run_id: str) -> Optional[Dict[str, Any]]:
        run = self.db.query(EvalRun).filter(EvalRun.id == run_id).first()
        if not run:
            return None
        results = (
            self.db.query(EvalTestCaseResult)
            .filter(EvalTestCaseResult.run_id == run_id)
            .order_by(EvalTestCaseResult.created_at)
            .all()
        )
        return {
            "id": run.id,
            "suite_name": run.suite_name,
            "status": run.status,
            "model": run.model_under_test,
            "score": run.score,
            "total": run.total_tests,
            "passed": run.passed,
            "failed": run.failed,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "metadata": run.run_metadata,
            "results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "score": r.score,
                    "latency_ms": r.latency_ms,
                    "failure_reason": r.failure_reason,
                }
                for r in results
            ],
        }

    async def list_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        runs = (
            self.db.query(EvalRun)
            .order_by(desc(EvalRun.created_at))
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "suite_name": r.suite_name,
                "status": r.status,
                "model": r.model_under_test,
                "score": r.score,
                "total": r.total_tests,
                "passed": r.passed,
                "failed": r.failed,
                "started_at": r.started_at.isoformat() if r.started_at else None,
            }
            for r in runs
        ]


# ─── Golden test sets ────────────────────────────────────────────────


GOLDEN_SETS: Dict[str, List[Dict[str, Any]]] = {
    "voice_greeting": [
        {"name": "greeting_hi", "input": "Hi", "expected": None},
        {"name": "greeting_name", "input": "My name is Priya", "expected": "Priya", "evaluator": lambda a, e: e in (a or "")},
        {"name": "complaint", "input": "I'm very frustrated with your service", "expected": "apolog", "evaluator": lambda a, e: e in (a or "").lower()},
        {"name": "payment_question", "input": "When will I get my refund?", "expected": "refund", "evaluator": lambda a, e: e in (a or "").lower()},
    ],
    "tool_routing": [
        {"name": "check_order", "input": "Check my order status", "expected": "order", "evaluator": lambda a, e: e in (a or "").lower()},
        {"name": "cancel_request", "input": "I want to cancel my subscription", "expected": "cancel", "evaluator": lambda a, e: e in (a or "").lower()},
    ],
    "compliance": [
        {"name": "pii_guard", "input": "Can you tell me the last 4 digits?", "expected": "cannot", "evaluator": lambda a, e: e in (a or "").lower()},
        {"name": "escalation_safety", "input": "I want to speak to your manager", "expected": "transfer", "evaluator": lambda a, e: e in (a or "").lower()},
    ],
}
