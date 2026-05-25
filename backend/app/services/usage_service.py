"""
Usage metering service — tracks, queries, and enforces usage limits per org.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.billing import UsageRecord, Subscription, SubscriptionStatus
from app.models.tenant import Organization
from app.core.config import settings


PLAN_LIMITS: Dict[str, Dict[str, float]] = {
    "free": {
        "call_minutes": 50,
        "call_count": 25,
        "stt_seconds": 300,
        "tts_seconds": 300,
        "llm_tokens": 50_000,
        "tool_calls": 100,
        "messages_sent": 50,
        "storage_mb": 50,
        "knowledge_docs": 10,
    },
    "professional": {
        "call_minutes": 2000,
        "call_count": 1000,
        "stt_seconds": 12000,
        "tts_seconds": 12000,
        "llm_tokens": 2_000_000,
        "tool_calls": 5000,
        "messages_sent": 2000,
        "storage_mb": 500,
        "knowledge_docs": 100,
    },
    "enterprise": {
        "call_minutes": float("inf"),
        "call_count": float("inf"),
        "stt_seconds": float("inf"),
        "tts_seconds": float("inf"),
        "llm_tokens": float("inf"),
        "tool_calls": float("inf"),
        "messages_sent": float("inf"),
        "storage_mb": float("inf"),
        "knowledge_docs": float("inf"),
    },
}


FEATURE_TIER_MAP: Dict[str, str] = {
    "ultravox_call_stages": "professional",
    "ultravox_http_tools": "professional",
    "ultravox_shared_secrets": "enterprise",
    "workflow_automation": "professional",
    "whatsapp_messaging": "professional",
    "sms_messaging": "professional",
    "custom_voice_cloning": "enterprise",
    "compliance_audit": "enterprise",
    "analytics_export": "professional",
    "multi_agent_swarm": "enterprise",
    "branded_join_url": "enterprise",
    "prior_call_inheritance": "professional",
    "deferred_messages": "professional",
    "rate_limiting_overrides": "enterprise",
}


class UsageService:
    def __init__(self, db: Session):
        self.db = db

    def _active_statuses(self) -> list[str]:
        return [SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIALING.value]

    def _billing_period(self, org_id: str) -> tuple[date, date]:
        sub = self.db.query(Subscription).filter(
            Subscription.organization_id == org_id,
            Subscription.status.in_(self._active_statuses()),
        ).first()
        if sub:
            return sub.billing_period_start, sub.billing_period_end
        today = date.today()
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1)
        else:
            end = today.replace(month=today.month + 1, day=1)
        return start, end

    def record_usage(
        self,
        organization_id: str,
        metric: str,
        quantity: float,
        unit: str = "count",
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UsageRecord:
        period_start, period_end = self._billing_period(organization_id)
        record = UsageRecord(
            organization_id=organization_id,
            session_id=session_id,
            agent_id=agent_id,
            metric=metric,
            quantity=quantity,
            unit=unit,
            billing_period_start=period_start,
            billing_period_end=period_end,
            metadata_json=metadata or {},
        )
        self.db.add(record)
        self.db.commit()
        return record

    def get_usage(
        self,
        organization_id: str,
        metric: Optional[str] = None,
    ) -> List[UsageRecord]:
        period_start, period_end = self._billing_period(organization_id)
        query = self.db.query(UsageRecord).filter(
            UsageRecord.organization_id == organization_id,
            UsageRecord.billing_period_start == period_start,
            UsageRecord.billing_period_end == period_end,
        )
        if metric:
            query = query.filter(UsageRecord.metric == metric)
        return query.order_by(UsageRecord.recorded_at.desc()).all()

    def get_usage_summary(self, organization_id: str) -> Dict[str, float]:
        records = self.get_usage(organization_id)
        summary: Dict[str, float] = {}
        for r in records:
            summary[r.metric] = summary.get(r.metric, 0) + r.quantity
        return summary

    def get_usage_and_limits(self, organization_id: str) -> Dict[str, Any]:
        sub = self.db.query(Subscription).filter(
            Subscription.organization_id == organization_id,
            Subscription.status.in_(self._active_statuses()),
        ).first()
        plan = sub.plan if sub else "free"
        usage = self.get_usage_summary(organization_id)
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

        # Trial info
        trial: Dict[str, Any] = {"active": False}
        if sub and sub.status == SubscriptionStatus.TRIALING.value:
            now = datetime.utcnow()
            if sub.trial_ends_at and now < sub.trial_ends_at:
                days_left = (sub.trial_ends_at - now).days
                trial = {
                    "active": True,
                    "starts_at": sub.trial_starts_at.isoformat() if sub.trial_starts_at else None,
                    "ends_at": sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
                    "days_remaining": max(days_left, 0),
                }
            else:
                trial = {"active": False, "expired": True}

        result: Dict[str, Any] = {
            "plan": plan,
            "usage": {},
            "limits": {},
            "percentages": {},
            "trial": trial,
        }
        for metric, limit in limits.items():
            used = usage.get(metric, 0)
            result["usage"][metric] = used
            result["limits"][metric] = limit
            if limit == float("inf"):
                result["percentages"][metric] = 0
            elif limit > 0:
                result["percentages"][metric] = round((used / limit) * 100, 2)
            else:
                result["percentages"][metric] = 0
        return result

    def check_limits(
        self,
        organization_id: str,
        metric: str,
        additional_quantity: float = 1,
    ) -> bool:
        """Return True if within limits, False if over."""
        summary = self.get_usage_and_limits(organization_id)
        # Check trial expiry first
        trial = summary.get("trial", {})
        if trial.get("expired"):
            return False
        limit = summary["limits"].get(metric, 0)
        used = summary["usage"].get(metric, 0)
        if limit == float("inf"):
            return True
        return (used + additional_quantity) <= limit

    def require_feature(self, organization_id: str, feature: str) -> bool:
        """Check if org's plan includes the given feature."""
        sub = self.db.query(Subscription).filter(
            Subscription.organization_id == organization_id,
            Subscription.status.in_(self._active_statuses()),
        ).first()
        plan = sub.plan if sub else "free"
        required = FEATURE_TIER_MAP.get(feature, "enterprise")
        tiers = ["free", "professional", "enterprise"]
        return tiers.index(plan) >= tiers.index(required)

    def check_call_allowed(self, organization_id: str) -> Dict[str, Any]:
        """Check if org can initiate a new call.

        Returns dict with 'allowed' (bool) and 'reason' (str or None).
        """
        sub = self.db.query(Subscription).filter(
            Subscription.organization_id == organization_id,
        ).first()
        if sub and sub.status == SubscriptionStatus.TRIALING.value:
            if sub.trial_ends_at and datetime.utcnow() > sub.trial_ends_at:
                return {"allowed": False, "reason": "trial_expired"}
        if not self.check_limits(organization_id, "call_minutes", 1):
            return {"allowed": False, "reason": "limit_exceeded"}
        return {"allowed": True, "reason": None}

    def record_call_usage(
        self,
        organization_id: str,
        session_id: str,
        agent_id: str,
        duration_seconds: float,
        stt_seconds: float = 0,
        tts_seconds: float = 0,
        llm_tokens: int = 0,
        llm_input_tokens: int = 0,
        llm_output_tokens: int = 0,
        tool_calls: int = 0,
    ) -> None:
        minutes = duration_seconds / 60
        self.record_usage(organization_id, "call_minutes", minutes, unit="minutes",
                          session_id=session_id, agent_id=agent_id)
        self.record_usage(organization_id, "call_count", 1, unit="count",
                          session_id=session_id, agent_id=agent_id)
        if stt_seconds > 0:
            self.record_usage(organization_id, "stt_seconds", stt_seconds, unit="seconds",
                              session_id=session_id, agent_id=agent_id)
        if tts_seconds > 0:
            self.record_usage(organization_id, "tts_seconds", tts_seconds, unit="seconds",
                              session_id=session_id, agent_id=agent_id)
        if llm_tokens > 0:
            self.record_usage(organization_id, "llm_tokens", llm_tokens, unit="tokens",
                              session_id=session_id, agent_id=agent_id)
        if llm_input_tokens > 0:
            self.record_usage(organization_id, "llm_input_tokens", llm_input_tokens, unit="tokens",
                              session_id=session_id, agent_id=agent_id)
        if llm_output_tokens > 0:
            self.record_usage(organization_id, "llm_output_tokens", llm_output_tokens, unit="tokens",
                              session_id=session_id, agent_id=agent_id)
        if tool_calls > 0:
            self.record_usage(organization_id, "tool_calls", tool_calls, unit="count",
                              session_id=session_id, agent_id=agent_id)

    def record_message_usage(
        self,
        organization_id: str,
        direction: str,
        count: int = 1,
        session_id: Optional[str] = None,
    ) -> None:
        metric = "messages_sent" if direction == "outbound" else "messages_received"
        self.record_usage(organization_id, metric, count,
                          session_id=session_id)
