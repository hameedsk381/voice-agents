"""Tests for billing, subscription, usage metering, and tier gating."""

from datetime import date
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.models.billing import Subscription, UsageRecord, RateCard, SubscriptionStatus, UsageMetric
from app.services.usage_service import UsageService, PLAN_LIMITS, FEATURE_TIER_MAP
from app.services.metering_service import MeteringService, DEFAULT_RATE_CARDS


def test_usage_metric_enum_values():
    assert UsageMetric.CALL_MINUTES.value == "call_minutes"
    assert UsageMetric.LLM_TOKENS.value == "llm_tokens"
    assert UsageMetric.TOOL_CALLS.value == "tool_calls"


def test_subscription_status_enum():
    assert SubscriptionStatus.ACTIVE.value == "active"
    assert SubscriptionStatus.PAST_DUE.value == "past_due"
    assert SubscriptionStatus.TRIALING.value == "trialing"


def test_plan_limits_have_keys():
    for plan in ("free", "professional", "enterprise"):
        assert plan in PLAN_LIMITS
        assert "call_minutes" in PLAN_LIMITS[plan]
        assert "call_count" in PLAN_LIMITS[plan]
        assert "llm_tokens" in PLAN_LIMITS[plan]


def test_enterprise_limits_infinite():
    assert PLAN_LIMITS["enterprise"]["call_minutes"] == float("inf")
    assert PLAN_LIMITS["enterprise"]["llm_tokens"] == float("inf")


def test_feature_tier_map():
    assert FEATURE_TIER_MAP["ultravox_call_stages"] == "professional"
    assert FEATURE_TIER_MAP["compliance_audit"] == "enterprise"
    assert FEATURE_TIER_MAP["whatsapp_messaging"] == "professional"


def test_default_rate_cards_have_all_plans():
    for plan in ("free", "professional", "enterprise"):
        assert plan in DEFAULT_RATE_CARDS


class TestUsageService:
    def test_billing_period_no_subscription(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = UsageService(db)
        start, end = svc._billing_period("org-1")
        assert start.day == 1
        assert end > start

    def test_billing_period_with_subscription(self):
        sub = MagicMock()
        sub.billing_period_start = date(2026, 1, 1)
        sub.billing_period_end = date(2026, 2, 1)
        sub.status = SubscriptionStatus.ACTIVE.value
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = sub
        svc = UsageService(db)
        start, end = svc._billing_period("org-1")
        assert start == date(2026, 1, 1)
        assert end == date(2026, 2, 1)

    def test_record_and_get_usage(self):
        db = MagicMock()
        sub = MagicMock()
        sub.billing_period_start = date(2026, 6, 1)
        sub.billing_period_end = date(2026, 7, 1)
        sub.status = SubscriptionStatus.ACTIVE.value
        db.query.return_value.filter.return_value.first.return_value = sub

        svc = UsageService(db)
        svc.record_usage("org-1", "call_minutes", 5.5, unit="minutes", session_id="sess-1")

        # Verify UsageRecord was added
        args = db.add.call_args[0]
        assert len(args) == 1
        record = args[0]
        assert isinstance(record, UsageRecord)
        assert record.organization_id == "org-1"
        assert record.metric == "call_minutes"
        assert record.quantity == 5.5
        assert record.session_id == "sess-1"
        db.commit.assert_called_once()

    def test_get_usage_summary(self):
        db = MagicMock()
        sub = MagicMock()
        sub.billing_period_start = date(2026, 6, 1)
        sub.billing_period_end = date(2026, 7, 1)
        sub.status = SubscriptionStatus.ACTIVE.value
        db.query.return_value.filter.return_value.first.return_value = sub

        r1 = MagicMock(spec=UsageRecord)
        r1.metric = "call_minutes"
        r1.quantity = 10
        r2 = MagicMock(spec=UsageRecord)
        r2.metric = "call_minutes"
        r2.quantity = 5
        r3 = MagicMock(spec=UsageRecord)
        r3.metric = "llm_tokens"
        r3.quantity = 1000

        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [r1, r2, r3]

        svc = UsageService(db)
        summary = svc.get_usage_summary("org-1")
        assert summary["call_minutes"] == 15
        assert summary["llm_tokens"] == 1000

    def test_check_limits_within(self):
        db = MagicMock()
        sub = MagicMock()
        sub.billing_period_start = date(2026, 6, 1)
        sub.billing_period_end = date(2026, 7, 1)
        sub.plan = "free"
        sub.status = SubscriptionStatus.ACTIVE.value
        db.query.return_value.filter.return_value.first.return_value = sub

        r = MagicMock(spec=UsageRecord)
        r.metric = "call_minutes"
        r.quantity = 50
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value = [r]

        svc = UsageService(db)
        assert svc.check_limits("org-1", "call_minutes", 10) is True

    def test_check_limits_exceeded(self):
        db = MagicMock()
        sub = MagicMock()
        sub.billing_period_start = date(2026, 6, 1)
        sub.billing_period_end = date(2026, 7, 1)
        sub.plan = "free"
        sub.status = SubscriptionStatus.ACTIVE.value
        db.query.return_value.filter.return_value.first.return_value = sub

        r = MagicMock(spec=UsageRecord)
        r.metric = "call_minutes"
        r.quantity = 95
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [r]

        svc = UsageService(db)
        assert svc.check_limits("org-1", "call_minutes", 10) is False

    def test_require_feature_free_cant_access_professional(self):
        db = MagicMock()
        sub = MagicMock()
        sub.plan = "free"
        sub.status = SubscriptionStatus.ACTIVE.value
        db.query.return_value.filter.return_value.first.return_value = sub

        svc = UsageService(db)
        assert svc.require_feature("org-1", "whatsapp_messaging") is False

    def test_require_feature_professional_can_access(self):
        db = MagicMock()
        sub = MagicMock()
        sub.plan = "professional"
        sub.status = SubscriptionStatus.ACTIVE.value
        db.query.return_value.filter.return_value.first.return_value = sub

        svc = UsageService(db)
        assert svc.require_feature("org-1", "whatsapp_messaging") is True

    def test_require_feature_enterprise_only_blocked_for_free(self):
        db = MagicMock()
        sub = MagicMock()
        sub.plan = "free"
        sub.status = SubscriptionStatus.ACTIVE.value
        db.query.return_value.filter.return_value.first.return_value = sub

        svc = UsageService(db)
        assert svc.require_feature("org-1", "compliance_audit") is False
        assert svc.require_feature("org-1", "custom_voice_cloning") is False

    def test_record_call_usage_records_multiple_metrics(self):
        db = MagicMock()
        sub = MagicMock()
        sub.billing_period_start = date(2026, 6, 1)
        sub.billing_period_end = date(2026, 7, 1)
        sub.status = SubscriptionStatus.ACTIVE.value
        db.query.return_value.filter.return_value.first.return_value = sub

        svc = UsageService(db)
        svc.record_call_usage(
            organization_id="org-1",
            session_id="sess-1",
            agent_id="agent-1",
            duration_seconds=300,
            stt_seconds=60,
            tts_seconds=45,
            llm_tokens=5000,
            tool_calls=3,
        )

        assert db.add.call_count >= 5  # call_minutes, call_count, stt, tts, llm, tools

    def test_record_message_usage(self):
        db = MagicMock()
        sub = MagicMock()
        sub.billing_period_start = date(2026, 6, 1)
        sub.billing_period_end = date(2026, 7, 1)
        sub.status = SubscriptionStatus.ACTIVE.value
        db.query.return_value.filter.return_value.first.return_value = sub

        svc = UsageService(db)
        svc.record_message_usage("org-1", "outbound", count=2, session_id="sess-1")
        svc.record_message_usage("org-1", "inbound", count=1, session_id="sess-1")

        calls = [c[0][0] for c in db.add.call_args_list]
        metrics = [c.metric for c in calls]
        assert "messages_sent" in metrics
        assert "messages_received" in metrics


class TestMeteringService:
    def test_get_rate_card_free(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = MeteringService(db)
        card = svc.get_rate_card("free")
        assert card["call_minutes"]["price_per_unit"] == 0
        assert card["call_minutes"]["included_units"] == 50

    def test_get_rate_card_professional(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = MeteringService(db)
        card = svc.get_rate_card("professional")
        assert card["call_minutes"]["price_per_unit"] == 0.05
        assert card["call_minutes"]["overage_price_per_unit"] == 0.08

    def test_calculate_cost_within_included(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = MeteringService(db)
        result = svc.calculate_cost("free", {"call_minutes": 50, "llm_tokens": 5000})
        assert result["total_cost"] == 0
        assert result["plan"] == "free"

    def test_calculate_cost_overage(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = MeteringService(db)
        result = svc.calculate_cost("professional", {"call_minutes": 2500})
        assert result["total_cost"] > 0
        assert result["breakdown"]["call_minutes"]["overage_units"] == 500

    def test_calculate_cost_exact_included(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = MeteringService(db)
        result = svc.calculate_cost("professional", {"call_minutes": 2000})
        base = 2000 * 0.05
        assert result["total_cost"] == base

    def test_calculate_cost_enterprise_no_overage(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = MeteringService(db)
        result = svc.calculate_cost("enterprise", {"call_minutes": 99999})
        expected = 99999 * 0.03
        assert abs(result["total_cost"] - expected) < 0.01

    def test_estimate_call_cost(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = MeteringService(db)
        cost = svc.estimate_call_cost("free", duration_minutes=50, stt_seconds=300, tts_seconds=200)
        assert cost == 0

        cost2 = svc.estimate_call_cost("professional", duration_minutes=2100)
        assert cost2 > 0

    def test_seed_default_rate_cards(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        svc = MeteringService(db)
        svc.seed_default_rate_cards()

        # Should add rate cards for each plan/metric combo
        total_cards = sum(len(metrics) for metrics in DEFAULT_RATE_CARDS.values())
        assert db.add.call_count == total_cards

    def test_seed_rate_cards_skips_existing(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = MagicMock()

        svc = MeteringService(db)
        svc.seed_default_rate_cards()

        db.add.assert_not_called()


def test_usage_and_limits_summary():
    db = MagicMock()
    sub = MagicMock()
    sub.billing_period_start = date(2026, 6, 1)
    sub.billing_period_end = date(2026, 7, 1)
    sub.plan = "free"
    sub.status = SubscriptionStatus.ACTIVE.value
    db.query.return_value.filter.return_value.first.return_value = sub

    r = MagicMock(spec=UsageRecord)
    r.metric = "call_minutes"
    r.quantity = 25
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [r]

    svc = UsageService(db)
    result = svc.get_usage_and_limits("org-1")
    assert result["plan"] == "free"
    assert result["usage"]["call_minutes"] == 25
    assert result["limits"]["call_minutes"] == 50
    assert result["percentages"]["call_minutes"] == 50.0


def test_usage_and_limits_enterprise():
    db = MagicMock()
    sub = MagicMock()
    sub.billing_period_start = date(2026, 6, 1)
    sub.billing_period_end = date(2026, 7, 1)
    sub.plan = "enterprise"
    sub.status = SubscriptionStatus.ACTIVE.value
    db.query.return_value.filter.return_value.first.return_value = sub

    svc = UsageService(db)
    result = svc.get_usage_and_limits("org-1")
    assert result["plan"] == "enterprise"
    assert result["limits"]["call_minutes"] == float("inf")
    assert result["percentages"]["call_minutes"] == 0


@pytest.mark.asyncio
async def test_analytics_service_records_usage():
    """Verify analytics service wires usage recording on call completion."""
    from app.services.analytics_service import AnalyticsService
    db = MagicMock()
    agent = MagicMock()
    agent.success_criteria = []
    agent.failure_conditions = []
    agent.goals = []

    svc = AnalyticsService(db)
    svc.usage = MagicMock()

    session_data = {
        "session_id": "sess-1",
        "agent_id": "agent-1",
        "org_id": "org-1",
        "start_time": "2026-01-01T00:00:00",
        "duration": 300,
        "tokens": 5000,
        "status": "completed",
        "reason": "normal",
        "transcript": [],
        "tool_calls": 3,
    }
    with patch.object(svc, "classify_outcome", return_value=("SUCCESS", "Done")):
        result = await svc.log_call_completion(session_data, agent)

    svc.usage.record_call_usage.assert_called_once_with(
        organization_id="org-1",
        session_id="sess-1",
        agent_id="agent-1",
        duration_seconds=300,
        stt_seconds=0,
        tts_seconds=0,
        llm_tokens=5000,
        tool_calls=3,
    )
    assert result is not None
