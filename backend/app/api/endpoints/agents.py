from datetime import datetime, timezone
from typing import List, Optional

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core import database
from app.core.deps import get_current_user_required
from app.models import agent as models
from app.models.analytics import CallLog
from app.models.compliance import AuditLog
from app.models.user import User
from app.orchestration.ultravox_call import merge_ultravox_config
from app.orchestration.websocket_proxy import is_ultravox_runtime
from app.schemas import agent as schemas
from app.schemas.policy import ConversationPolicy
from app.services.analytics_service import AnalyticsService
from app.services.compliance_service import get_baseline_rules
from app.services.ultravox_agent_sync import (
    delete_ultravox_agent_for_voise_agent,
    sync_agent_to_ultravox,
)

router = APIRouter()


async def _persist_ultravox_sync(db_agent: models.Agent, db: Session) -> None:
    if not is_ultravox_runtime():
        return
    try:
        uv_id = await sync_agent_to_ultravox(db_agent)
        if uv_id:
            db_agent.config = merge_ultravox_config(
                db_agent.config,
                ultravox_agent_id=uv_id,
                synced_at=datetime.now(timezone.utc).isoformat(),
            )
            db.commit()
            db.refresh(db_agent)
    except Exception as exc:
        logger.warning(f"Ultravox sync deferred for agent {db_agent.id}: {exc}")


@router.post("/", response_model=schemas.Agent)
async def create_agent(
    agent: schemas.AgentCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    db_agent = models.Agent(
        id=str(uuid.uuid4()),
        name=agent.name,
        role=agent.role,
        description=agent.description,
        persona=agent.persona,
        language=agent.language,
        tools=agent.tools,
        goals=agent.goals,
        success_criteria=agent.success_criteria,
        failure_conditions=agent.failure_conditions,
        exit_actions=agent.exit_actions,
        is_active=agent.is_active,
        token_limit=agent.token_limit,
        fallback_model=agent.fallback_model,
        organization_id=agent.organization_id or current_user.organization_id,
        config=agent.config,
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    await _persist_ultravox_sync(db_agent, db)
    return db_agent


@router.get("/", response_model=List[schemas.Agent])
def read_agents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    q = db.query(models.Agent)
    if current_user.organization_id:
        q = q.filter(models.Agent.organization_id == current_user.organization_id)
    agents = q.offset(skip).limit(limit).all()
    return agents


@router.get("/{agent_id}", response_model=schemas.Agent)
def read_agent(
    agent_id: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    q = db.query(models.Agent).filter(models.Agent.id == agent_id)
    if current_user.organization_id:
        q = q.filter(models.Agent.organization_id == current_user.organization_id)
    agent = q.first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=schemas.Agent)
async def update_agent(
    agent_id: str,
    agent_update: schemas.AgentUpdate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    q = db.query(models.Agent).filter(models.Agent.id == agent_id)
    if current_user.organization_id:
        q = q.filter(models.Agent.organization_id == current_user.organization_id)
    db_agent = q.first()
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    update_data = agent_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_agent, key, value)

    db.commit()
    db.refresh(db_agent)
    await _persist_ultravox_sync(db_agent, db)
    return db_agent


@router.post("/{agent_id}/sync-ultravox", response_model=schemas.Agent)
async def sync_ultravox_agent(
    agent_id: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Push the latest Voise agent config to the linked Ultravox Agent template."""
    if not is_ultravox_runtime():
        raise HTTPException(
            status_code=503,
            detail="Ultravox is not configured. Set ULTRAVOX_API_KEY and VOICE_RUNTIME=ultravox.",
        )

    q = db.query(models.Agent).filter(models.Agent.id == agent_id)
    if current_user.organization_id:
        q = q.filter(models.Agent.organization_id == current_user.organization_id)
    db_agent = q.first()
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    uv_id = await sync_agent_to_ultravox(db_agent)
    if not uv_id:
        raise HTTPException(status_code=502, detail="Ultravox agent sync failed")

    db_agent.config = merge_ultravox_config(
        db_agent.config,
        ultravox_agent_id=uv_id,
        synced_at=datetime.now(timezone.utc).isoformat(),
    )
    db.commit()
    db.refresh(db_agent)
    return db_agent


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    q = db.query(models.Agent).filter(models.Agent.id == agent_id)
    if current_user.organization_id:
        q = q.filter(models.Agent.organization_id == current_user.organization_id)
    db_agent = q.first()
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    await delete_ultravox_agent_for_voise_agent(db_agent)
    db.delete(db_agent)
    db.commit()
    return {"ok": True}


@router.post("/{agent_id}/versions", response_model=schemas.AgentVersion)
def create_agent_version(
    agent_id: str,
    version_data: schemas.AgentVersionCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Create a new snapshot/version of an agent."""
    q = db.query(models.Agent).filter(models.Agent.id == agent_id)
    if current_user.organization_id:
        q = q.filter(models.Agent.organization_id == current_user.organization_id)
    db_agent = q.first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    db_version = models.AgentVersion(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        version_number=version_data.version_number,
        persona=version_data.persona,
        tools=version_data.tools,
        policy=version_data.policy,
        success_criteria=version_data.success_criteria,
        failure_conditions=version_data.failure_conditions,
        exit_actions=version_data.exit_actions,
        change_log=version_data.change_log,
        token_limit=version_data.token_limit,
        fallback_model=version_data.fallback_model,
    )
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version


@router.get("/{agent_id}/versions", response_model=List[schemas.AgentVersion])
def get_agent_versions(
    agent_id: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """List all versions for an agent."""
    q = db.query(models.Agent).filter(models.Agent.id == agent_id)
    if current_user.organization_id:
        q = q.filter(models.Agent.organization_id == current_user.organization_id)
    if not q.first():
        raise HTTPException(status_code=404, detail="Agent not found")
    return (
        db.query(models.AgentVersion)
        .filter(models.AgentVersion.agent_id == agent_id)
        .order_by(models.AgentVersion.version_number.desc())
        .all()
    )


@router.post("/{agent_id}/pin/{version_id}")
async def pin_agent_version(
    agent_id: str,
    version_id: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Pin the agent to a specific version and re-sync the Ultravox Agent template."""
    q = db.query(models.Agent).filter(models.Agent.id == agent_id)
    if current_user.organization_id:
        q = q.filter(models.Agent.organization_id == current_user.organization_id)
    db_agent = q.first()
    db_version = db.query(models.AgentVersion).filter(models.AgentVersion.id == version_id).first()

    if not db_agent or not db_version:
        raise HTTPException(status_code=404, detail="Agent or Version not found")

    db_agent.active_version_id = version_id
    db.commit()
    db.refresh(db_agent)

    if is_ultravox_runtime():
        try:
            uv_id = await sync_agent_to_ultravox(
                db_agent,
                active_persona=db_version.persona,
                active_tools=db_version.tools,
            )
            if uv_id:
                db_agent.config = merge_ultravox_config(
                    db_agent.config,
                    ultravox_agent_id=uv_id,
                    synced_at=datetime.now(timezone.utc).isoformat(),
                )
                db.commit()
        except Exception as exc:
            logger.warning(
                f"Ultravox sync after pin failed for agent {agent_id}: {exc}"
            )

    return {"status": "pinned", "version": db_version.version_number}


@router.get("/{agent_id}/analytics")
async def get_agent_analytics(
    agent_id: str,
    days: int = Query(7, description="Number of days for trend data"),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Get per-agent analytics: overview metrics + daily call trends."""
    q = db.query(models.Agent).filter(models.Agent.id == agent_id)
    if current_user.organization_id:
        q = q.filter(models.Agent.organization_id == current_user.organization_id)
    db_agent = q.first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    svc = AnalyticsService(db)

    total_calls = db.query(func.count(CallLog.id)).filter(CallLog.agent_id == agent_id).scalar() or 0
    total_duration = db.query(func.sum(CallLog.duration_seconds)).filter(CallLog.agent_id == agent_id).scalar() or 0
    avg_latency = db.query(func.avg(CallLog.avg_latency_ms)).filter(CallLog.agent_id == agent_id).scalar() or 0
    total_cost = db.query(func.sum(CallLog.estimated_cost)).filter(CallLog.agent_id == agent_id).scalar() or 0
    successful = db.query(func.count(CallLog.id)).filter(CallLog.agent_id == agent_id, CallLog.outcome == "SUCCESS").scalar() or 0
    success_rate = (successful / total_calls * 100) if total_calls > 0 else 0

    outcome_counts = db.query(CallLog.outcome, func.count(CallLog.id).label("count")).filter(
        CallLog.agent_id == agent_id
    ).group_by(CallLog.outcome).all()

    # Daily trends for this agent
    from datetime import datetime as dt, timedelta
    start_date = dt.utcnow() - timedelta(days=days)
    daily = db.query(
        func.date(CallLog.start_time).label("date"),
        func.count(CallLog.id).label("count"),
    ).filter(
        CallLog.agent_id == agent_id,
        CallLog.start_time >= start_date,
    ).group_by(func.date(CallLog.start_time)).order_by("date").all()

    return {
        "total_calls": total_calls,
        "total_minutes": round(total_duration / 60, 2),
        "avg_duration_seconds": round(total_duration / total_calls, 1) if total_calls > 0 else 0,
        "avg_latency_ms": round(avg_latency, 1),
        "total_cost": round(total_cost, 4),
        "success_rate": round(success_rate, 1),
        "outcome_breakdown": {r.outcome or "unknown": r.count for r in outcome_counts},
        "daily_trends": [{"date": str(r.date), "count": r.count} for r in daily],
    }


@router.get("/{agent_id}/calls")
def get_agent_calls(
    agent_id: str,
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Get recent call logs for a specific agent."""
    q = db.query(models.Agent).filter(models.Agent.id == agent_id)
    if current_user.organization_id:
        q = q.filter(models.Agent.organization_id == current_user.organization_id)
    db_agent = q.first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    calls = db.query(CallLog).filter(
        CallLog.agent_id == agent_id
    ).order_by(CallLog.start_time.desc()).offset(offset).limit(limit).all()

    return [
        {
            "id": c.id,
            "session_id": c.session_id,
            "caller_id": c.caller_id,
            "duration_seconds": c.duration_seconds,
            "avg_latency_ms": c.avg_latency_ms,
            "total_turns": c.total_turns,
            "total_tokens": c.total_tokens,
            "estimated_cost": c.estimated_cost,
            "outcome": c.outcome,
            "end_reason": c.end_reason,
            "start_time": c.start_time.isoformat() if c.start_time else None,
        }
        for c in calls
    ]


@router.get("/{agent_id}/policy")
def get_agent_policy(
    agent_id: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Get the current conversation policy for an agent."""
    q = db.query(models.Agent).filter(models.Agent.id == agent_id)
    if current_user.organization_id:
        q = q.filter(models.Agent.organization_id == current_user.organization_id)
    db_agent = q.first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    policy_raw = db_agent.config.get("policy") if db_agent.config else None
    if not policy_raw:
        return {
            "version": "1.0",
            "initial_state": "opening",
            "states": {},
            "global_guardrails": [],
        }
    return policy_raw


@router.put("/{agent_id}/policy")
def update_agent_policy(
    agent_id: str,
    policy: dict,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Update the conversation policy for an agent."""
    q = db.query(models.Agent).filter(models.Agent.id == agent_id)
    if current_user.organization_id:
        q = q.filter(models.Agent.organization_id == current_user.organization_id)
    db_agent = q.first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    config = db_agent.config or {}
    config["policy"] = policy
    db_agent.config = config
    db.commit()
    db.refresh(db_agent)
    return {"ok": True}


@router.get("/{agent_id}/compliance")
def get_agent_compliance(
    agent_id: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Get compliance summary for an agent's calls."""
    q = db.query(models.Agent).filter(models.Agent.id == agent_id)
    if current_user.organization_id:
        q = q.filter(models.Agent.organization_id == current_user.organization_id)
    db_agent = q.first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    total_audited = db.query(func.count(AuditLog.id)).filter(AuditLog.agent_id == agent_id).scalar() or 0
    total_violations = db.query(func.count(AuditLog.id)).filter(
        AuditLog.agent_id == agent_id, AuditLog.is_compliant == False
    ).scalar() or 0
    max_risk = db.query(func.max(AuditLog.risk_score)).filter(AuditLog.agent_id == agent_id).scalar() or 0

    recent_violations = db.query(AuditLog).filter(
        AuditLog.agent_id == agent_id, AuditLog.is_compliant == False
    ).order_by(AuditLog.created_at.desc()).limit(10).all()

    rules = get_baseline_rules()

    return {
        "total_turns_audited": total_audited,
        "total_violations": total_violations,
        "max_risk_score": round(max_risk, 2),
        "is_compliant": total_violations == 0,
        "recent_violations": [
            {
                "turn_index": v.turn_index,
                "violations": v.violations,
                "risk_score": v.risk_score,
                "state_name": v.state_name,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in recent_violations
        ],
        "active_rules": [
            {"id": r.id, "name": r.name, "description": r.description, "severity": r.severity.value}
            for r in rules
        ],
    }
