"""
Tier gating and feature enforcement dependencies.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import database
from app.core.deps import get_current_user_required
from app.models.user import User
from app.models.billing import Subscription, SubscriptionStatus


TIER_ORDER = ["free", "professional", "enterprise"]


def get_org_plan(db: Session, organization_id: str) -> str:
    sub = db.query(Subscription).filter(
        Subscription.organization_id == organization_id,
        Subscription.status == SubscriptionStatus.ACTIVE.value,
    ).first()
    if sub:
        return sub.plan
    return "free"


def require_tier(min_tier: str):
    """FastAPI dependency factory: require org to have at least min_tier plan.

    Usage:
        @router.get("/feature", dependencies=[Depends(require_tier("professional"))])
    """
    if min_tier not in TIER_ORDER:
        raise ValueError(f"Unknown tier: {min_tier}")

    async def _gate(
        current_user: User = Depends(get_current_user_required),
        db: Session = Depends(database.get_db),
    ) -> None:
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No organization associated with this user.",
            )
        plan = get_org_plan(db, org_id)
        if TIER_ORDER.index(plan) < TIER_ORDER.index(min_tier):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    f"This feature requires the '{min_tier}' plan or above. "
                    f"Your current plan is '{plan}'. "
                    "Please upgrade to access this feature."
                ),
            )

    return _gate


def require_feature(feature: str):
    """FastAPI dependency factory: require org's plan to include a specific feature.

    Usage:
        @router.get("/stages", dependencies=[Depends(require_feature("ultravox_call_stages"))])
    """
    from app.services.usage_service import FEATURE_TIER_MAP

    min_tier = FEATURE_TIER_MAP.get(feature, "enterprise")

    async def _gate(
        current_user: User = Depends(get_current_user_required),
        db: Session = Depends(database.get_db),
    ) -> None:
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No organization associated with this user.",
            )
        plan = get_org_plan(db, org_id)
        if TIER_ORDER.index(plan) < TIER_ORDER.index(min_tier):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    f"Feature '{feature}' requires the '{min_tier}' plan or above. "
                    f"Your current plan is '{plan}'."
                ),
            )

    return _gate
