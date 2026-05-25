"""
Billing, subscription, and usage metering API endpoints.
"""
from datetime import date, datetime
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core import database
from app.core.deps import get_current_user_required
from app.core.tier_gate import get_org_plan
from app.models.user import User
from app.models.billing import Subscription, SubscriptionStatus
from app.services.usage_service import UsageService
from app.services.metering_service import MeteringService

router = APIRouter()


class UsageRecordRequest(BaseModel):
    metric: str
    quantity: float
    unit: str = "count"
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SubscriptionUpdate(BaseModel):
    plan: str
    status: Optional[str] = None
    auto_renew: Optional[str] = None
    billing_period_start: Optional[str] = None
    billing_period_end: Optional[str] = None


@router.get("/usage")
async def get_usage(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Get current billing period usage summary and limits."""
    svc = UsageService(db)
    return svc.get_usage_and_limits(current_user.organization_id)


@router.get("/usage/records")
async def list_usage_records(
    metric: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """List individual usage records for the current billing period."""
    svc = UsageService(db)
    records = svc.get_usage(current_user.organization_id, metric=metric)
    return {
        "records": [
            {
                "id": r.id,
                "metric": r.metric,
                "quantity": r.quantity,
                "unit": r.unit,
                "session_id": r.session_id,
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            }
            for r in records
        ],
        "total": len(records),
    }


@router.post("/usage/record")
async def record_usage(
    data: UsageRecordRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Record a usage event for the current organization (internal)."""
    svc = UsageService(db)
    record = svc.record_usage(
        organization_id=current_user.organization_id,
        metric=data.metric,
        quantity=data.quantity,
        unit=data.unit,
        session_id=data.session_id,
        agent_id=data.agent_id,
        metadata=data.metadata,
    )
    return {"id": record.id, "metric": record.metric, "quantity": record.quantity}


@router.get("/rate-card")
async def get_rate_card(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Get the rate card for the current organization's plan."""
    plan = get_org_plan(db, current_user.organization_id)
    svc = MeteringService(db)
    return {"plan": plan, "rates": svc.get_rate_card(plan)}


@router.get("/cost/estimate")
async def estimate_call_cost(
    duration_minutes: float = Query(0, ge=0),
    stt_seconds: float = Query(0, ge=0),
    tts_seconds: float = Query(0, ge=0),
    llm_tokens: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Estimate the cost of a call based on current rate card."""
    plan = get_org_plan(db, current_user.organization_id)
    svc = MeteringService(db)
    cost = svc.estimate_call_cost(
        plan=plan,
        duration_minutes=duration_minutes,
        stt_seconds=stt_seconds,
        tts_seconds=tts_seconds,
        llm_tokens=llm_tokens,
    )
    return {"plan": plan, "estimated_cost": cost}


@router.get("/subscription")
async def get_subscription(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Get the current subscription details."""
    sub = db.query(Subscription).filter(
        Subscription.organization_id == current_user.organization_id,
    ).first()
    if not sub:
        return {
            "plan": "free",
            "status": "active",
            "billing_period_start": date.today().replace(day=1).isoformat(),
            "billing_period_end": None,
        }
    trial_info = None
    if sub.trial_starts_at or sub.trial_ends_at:
        trial_info = {
            "starts_at": sub.trial_starts_at.isoformat() if sub.trial_starts_at else None,
            "ends_at": sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
        }

    return {
        "id": sub.id,
        "plan": sub.plan,
        "status": sub.status,
        "billing_period_start": sub.billing_period_start.isoformat(),
        "billing_period_end": sub.billing_period_end.isoformat(),
        "auto_renew": sub.auto_renew,
        "trial": trial_info,
        "created_at": sub.created_at.isoformat() if sub.created_at else None,
    }


@router.put("/subscription")
async def update_subscription(
    data: SubscriptionUpdate,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Create or update the subscription for the current organization."""
    sub = db.query(Subscription).filter(
        Subscription.organization_id == current_user.organization_id,
    ).first()

    if data.billing_period_start:
        start = datetime.strptime(data.billing_period_start, "%Y-%m-%d").date()
    else:
        start = date.today().replace(day=1)

    if data.billing_period_end:
        end = datetime.strptime(data.billing_period_end, "%Y-%m-%d").date()
    else:
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1, day=1)
        else:
            end = start.replace(month=start.month + 1, day=1)

    if sub:
        sub.plan = data.plan
        if data.status:
            sub.status = data.status
        if data.auto_renew:
            sub.auto_renew = data.auto_renew
        sub.billing_period_start = start
        sub.billing_period_end = end
    else:
        sub = Subscription(
            organization_id=current_user.organization_id,
            plan=data.plan,
            status=data.status or SubscriptionStatus.ACTIVE.value,
            billing_period_start=start,
            billing_period_end=end,
            auto_renew=data.auto_renew or "true",
        )
        db.add(sub)

    db.commit()
    db.refresh(sub)

    return {
        "id": sub.id,
        "plan": sub.plan,
        "status": sub.status,
        "billing_period_start": sub.billing_period_start.isoformat(),
        "billing_period_end": sub.billing_period_end.isoformat(),
    }


@router.get("/limits")
async def check_usage_limits(
    metric: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Check current usage against plan limits."""
    svc = UsageService(db)
    if metric:
        return {
            "metric": metric,
            "within_limits": svc.check_limits(current_user.organization_id, metric),
        }
    return svc.get_usage_and_limits(current_user.organization_id)


@router.post("/limits/check")
async def check_limits_before_action(
    metric: str,
    additional_quantity: float = Query(1, ge=0),
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Check if an action would exceed usage limits before executing it."""
    svc = UsageService(db)
    allowed = svc.check_limits(
        current_user.organization_id,
        metric,
        additional_quantity=additional_quantity,
    )
    return {
        "allowed": allowed,
        "metric": metric,
        "additional_quantity": additional_quantity,
    }
