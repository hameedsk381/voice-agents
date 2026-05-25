from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.analytics import TraceLog, EvalRun, EvalTestCaseResult
from app.services.evaluation_service import EvaluationService, GOLDEN_SETS
from app.services.llm.groq_provider import GroqLLM

router = APIRouter()


# ─── Traces ────────────────────────────────────────────────────────────


@router.get("/traces")
def list_traces(
    session_id: Optional[str] = Query(None),
    span_type: Optional[str] = Query(None),
    span_name: Optional[str] = Query(None),
    status_code: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(TraceLog)
    if session_id:
        q = q.filter(TraceLog.session_id == session_id)
    if span_type:
        q = q.filter(TraceLog.span_type == span_type)
    if span_name:
        q = q.filter(TraceLog.span_name.ilike(f"%{span_name}%"))
    if status_code:
        q = q.filter(TraceLog.status_code == status_code)
    if agent_id:
        q = q.filter(TraceLog.agent_id == agent_id)
    total = q.count()
    rows = q.order_by(desc(TraceLog.created_at)).offset(offset).limit(limit).all()
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": [
            {
                "id": r.id,
                "session_id": r.session_id,
                "parent_span_id": r.parent_span_id,
                "span_name": r.span_name,
                "span_type": r.span_type,
                "duration_ms": r.duration_ms,
                "status_code": r.status_code,
                "status_message": r.status_message,
                "agent_id": r.agent_id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "attributes": r.attributes,
            }
            for r in rows
        ],
    }


@router.get("/traces/summary")
def trace_summary(
    since_hours: int = Query(24, le=168),
    db: Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(hours=since_hours)
    q = db.query(TraceLog).filter(TraceLog.created_at >= since)
    total = q.count()

    by_type = (
        db.query(
            TraceLog.span_type,
            func.count(TraceLog.id).label("count"),
            func.avg(TraceLog.duration_ms).label("avg_duration_ms"),
        )
        .filter(TraceLog.created_at >= since)
        .group_by(TraceLog.span_type)
        .all()
    )

    errors = q.filter(TraceLog.status_code != "OK").count()
    avg_duration = q.with_entities(func.avg(TraceLog.duration_ms)).scalar() or 0

    return {
        "total_spans": total,
        "error_spans": errors,
        "error_rate": round(errors / total * 100, 2) if total > 0 else 0,
        "avg_duration_ms": round(avg_duration, 2),
        "since_hours": since_hours,
        "by_type": [
            {
                "span_type": r.span_type,
                "count": r.count,
                "avg_duration_ms": round(r.avg_duration_ms, 2) if r.avg_duration_ms else 0,
            }
            for r in by_type
        ],
    }


# ─── Failure Modes ────────────────────────────────────────────────────


@router.get("/failures")
def list_failures(
    span_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(TraceLog).filter(TraceLog.status_code != "OK")
    if span_type:
        q = q.filter(TraceLog.span_type == span_type)
    rows = q.order_by(desc(TraceLog.created_at)).limit(limit).all()

    agg = (
        db.query(
            TraceLog.span_name,
            TraceLog.status_message,
            func.count(TraceLog.id).label("count"),
            func.avg(TraceLog.duration_ms).label("avg_duration_ms"),
        )
        .filter(TraceLog.status_code != "OK")
        .group_by(TraceLog.span_name, TraceLog.status_message)
        .order_by(desc(func.count(TraceLog.id)))
        .limit(20)
        .all()
    )

    return {
        "recent": [
            {
                "id": r.id,
                "session_id": r.session_id,
                "span_name": r.span_name,
                "span_type": r.span_type,
                "status_message": r.status_message,
                "duration_ms": r.duration_ms,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "aggregated": [
            {
                "span_name": r.span_name,
                "status_message": r.status_message,
                "count": r.count,
                "avg_duration_ms": round(r.avg_duration_ms, 2) if r.avg_duration_ms else 0,
            }
            for r in agg
        ],
    }


# ─── Eval ─────────────────────────────────────────────────────────────


@router.get("/eval/runs")
async def list_eval_runs(limit: int = Query(20, le=100), db: Session = Depends(get_db)):
    svc = EvaluationService(db)
    return await svc.list_runs(limit=limit)


@router.get("/eval/runs/{run_id}")
async def get_eval_run(run_id: str, db: Session = Depends(get_db)):
    svc = EvaluationService(db)
    return await svc.get_run_summary(run_id)


@router.post("/eval/runs")
async def trigger_eval_run(
    suite_name: str,
    model: str = Query("llama-3.3-70b-versatile"),
    db: Session = Depends(get_db),
):
    svc = EvaluationService(db)
    test_cases = GOLDEN_SETS.get(suite_name)
    if not test_cases:
        return {"error": f"Unknown suite '{suite_name}'. Available: {list(GOLDEN_SETS.keys())}"}

    llm = GroqLLM(model=model)

    async def inference(prompt: str, system_prompt: str) -> str:
        return await llm.generate_response(prompt, system_prompt, [])

    run = await svc.run_golden_suite(suite_name, model, test_cases, inference)
    return await svc.get_run_summary(run.id)


@router.get("/eval/suites")
def list_eval_suites():
    return {
        "suites": [
            {
                "name": name,
                "test_count": len(cases),
                "description": _suite_description(name),
            }
            for name, cases in GOLDEN_SETS.items()
        ]
    }


def _suite_description(name: str) -> str:
    descriptions = {
        "voice_greeting": "Tests agent greeting, name capture, complaint handling, and payment queries",
        "tool_routing": "Tests correct tool selection for order checks and cancellations",
        "compliance": "Tests PII protection and escalation safety",
    }
    return descriptions.get(name, name)
