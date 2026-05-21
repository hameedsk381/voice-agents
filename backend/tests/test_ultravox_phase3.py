"""Ultravox Agents Phase 3 — toolOverrides, callbacks, webhooks."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestration.ultravox_call import (
    build_call_callbacks,
    build_tool_overrides,
    merge_call_overrides,
    resolve_call_greeting,
)
from app.services.ultravox_webhook_service import verify_ultravox_webhook


def test_build_tool_overrides_data_connection():
    overrides = build_tool_overrides(["get_order_status"], implementation="dataConnection")
    assert "toolOverrides" in overrides
    assert overrides["toolOverrides"]["add"][0]["temporaryTool"]["dataConnection"] == {}


def test_merge_call_overrides():
    merged = merge_call_overrides(
        {"toolOverrides": {"add": []}},
        {"medium": {"twilio": {}}},
    )
    assert "toolOverrides" in merged and "medium" in merged


def test_resolve_call_greeting_campaign_wins():
    agent = MagicMock()
    agent.config = {"greeting": "Agent hi"}
    greeting = resolve_call_greeting(agent, campaign_call_config={"greeting": "Campaign hi"})
    assert greeting == "Campaign hi"


def test_build_call_callbacks_when_enabled():
    with patch("app.orchestration.ultravox_call.settings") as mock_settings:
        mock_settings.ULTRAVOX_CALLBACKS_ENABLED = True
        mock_settings.ULTRAVOX_CALLBACK_SECRET = "secret"
        with patch(
            "app.orchestration.ultravox_call.ultravox_call_ended_webhook_url",
            return_value="https://api.example.com/api/v1/ultravox/webhooks/call-ended",
        ):
            callbacks = build_call_callbacks()
    assert callbacks is not None
    assert callbacks["ended"]["url"].endswith("/call-ended")
    assert callbacks["ended"]["secrets"] == ["secret"]


def test_verify_ultravox_webhook_signature():
    import hmac

    secret = "test-secret"
    body = b'{"event":"call.ended","call":{"callId":"c1"}}'
    timestamp = "2026-05-21T12:00:00+00:00"
    expected = hmac.new(secret.encode(), body + timestamp.encode(), "sha256").hexdigest()

    request = MagicMock()
    request.headers = {
        "X-Ultravox-Webhook-Timestamp": timestamp,
        "X-Ultravox-Webhook-Signature": expected,
    }

    with patch("app.services.ultravox_webhook_service.settings") as mock_settings:
        mock_settings.ULTRAVOX_CALLBACK_SECRET = secret
        verify_ultravox_webhook(request, body)


@pytest.mark.asyncio
async def test_webhook_handle_call_ended():
    from app.services.ultravox_webhook_service import UltravoxWebhookService

    mock_db = MagicMock()
    mock_agent = MagicMock()
    mock_agent.id = "a1"
    mock_agent.success_criteria = []
    mock_agent.failure_conditions = []
    mock_agent.goals = []
    mock_db.query.return_value.filter.return_value.first.return_value = mock_agent

    session = {
        "session_id": "sess-1",
        "agent_id": "a1",
        "caller_id": "+1",
        "created_at": "2026-05-21T10:00:00",
        "history": [],
        "metadata": {},
        "status": "active",
    }

    with patch(
        "app.services.ultravox_webhook_service.session_manager.resolve_session_id_by_ultravox_call",
        new_callable=AsyncMock,
        return_value="sess-1",
    ), patch(
        "app.services.ultravox_webhook_service.session_manager.get_session",
        new_callable=AsyncMock,
        return_value=session,
    ), patch(
        "app.services.ultravox_webhook_service.session_manager.end_session",
        new_callable=AsyncMock,
    ), patch(
        "app.services.ultravox_webhook_service.session_manager.update_session",
        new_callable=AsyncMock,
    ), patch(
        "app.services.ultravox_webhook_service.monitoring_service.broadcast_event",
        new_callable=AsyncMock,
    ), patch.object(
        UltravoxWebhookService,
        "__init__",
        lambda self, db: None,
    ):
        service = UltravoxWebhookService(mock_db)
        service.ultravox = AsyncMock()
        service.ultravox.get_call = AsyncMock(return_value={"messages": []})
        service.db = mock_db

        with patch(
            "app.services.ultravox_webhook_service.AnalyticsService"
        ) as mock_analytics_cls:
            mock_analytics = mock_analytics_cls.return_value
            mock_log = MagicMock()
            mock_log.outcome = "NEUTRAL"
            mock_analytics.log_call_completion = AsyncMock(return_value=mock_log)

            result = await service.handle_call_ended(
                {"call": {"callId": "uv-call-1", "endReason": "hangup"}}
            )

    assert result["matched"] is True
    assert result["session_id"] == "sess-1"
