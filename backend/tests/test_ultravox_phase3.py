"""Ultravox Agents Phase 3 — toolOverrides, callbacks, webhooks."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestration.ultravox_call import (
    STAGE_CHANGE_TOOL_NAME,
    build_call_callbacks,
    build_retention_policy,
    build_shared_secrets,
    build_stage_change_tool_descriptor,
    build_stage_response,
    build_tool_overrides,
    build_tool_result,
    get_agent_stages,
    merge_call_overrides,
    resolve_call_greeting,
    resolve_stage_config,
)
from app.schemas.orchestrator import InactivityMessage, StageDefinition, UltravoxJoinRequest
from app.services.ultravox_webhook_service import verify_ultravox_webhook


def test_tool_result_with_guidance():
    result = build_tool_result(
        {"status": "ok", "data": "123"},
        response_type="tool-response",
        agent_reaction="speaks-once",
        call_state={"step": "confirmed"},
    )
    assert result["_response_type"] == "tool-response"
    assert result["_agent_reaction"] == "speaks-once"
    assert result["_call_state"] == {"step": "confirmed"}
    assert result["status"] == "ok"
    assert result["data"] == "123"


def test_tool_result_minimal():
    result = build_tool_result({"status": "ok"})
    assert result["status"] == "ok"
    assert "_response_type" not in result


def test_tool_overrides_remove():
    overrides = build_tool_overrides(
        tools=["check_loan_emi"],
        implementation="client",
        tools_remove=["old_tool_name", "legacy_tool_name"],
    )
    assert "toolOverrides" in overrides
    assert "add" in overrides["toolOverrides"]
    assert "remove" in overrides["toolOverrides"]
    assert overrides["toolOverrides"]["add"][0]["temporaryTool"]["modelToolName"] == "check_loan_emi"
    assert "old_tool_name" in overrides["toolOverrides"]["remove"]


def test_tool_overrides_replace():
    overrides = build_tool_overrides(
        tools_remove=["old_tool"],
        tools_replace=["check_loan_emi"],
        implementation="client",
    )
    assert "toolOverrides" in overrides
    assert "replace" in overrides["toolOverrides"]
    assert "add" not in overrides["toolOverrides"]
    assert "remove" not in overrides["toolOverrides"]


def test_build_shared_secrets():
    with patch("app.orchestration.ultravox_call.settings") as mock_settings:
        mock_settings.ULTRAVOX_SHARED_SECRETS = "secret1,secret2, secret3"
        secrets = build_shared_secrets()
    assert secrets == ["secret1", "secret2", "secret3"]


def test_build_shared_secrets_empty():
    with patch("app.orchestration.ultravox_call.settings") as mock_settings:
        mock_settings.ULTRAVOX_SHARED_SECRETS = None
        assert build_shared_secrets() is None


def test_build_retention_policy():
    with patch("app.orchestration.ultravox_call.settings") as mock_settings:
        mock_settings.ULTRAVOX_RETENTION_POLICY = "CALL_RETENTION_POLICY_AUTO_DELETE"
        assert build_retention_policy() == "CALL_RETENTION_POLICY_AUTO_DELETE"


def test_build_retention_policy_invalid():
    with patch("app.orchestration.ultravox_call.settings") as mock_settings:
        mock_settings.ULTRAVOX_RETENTION_POLICY = "INVALID"
        assert build_retention_policy() is None
    assert build_retention_policy("CALL_RETENTION_POLICY_RETAIN") == "CALL_RETENTION_POLICY_RETAIN"


def test_ultravox_join_request_with_overrides():
    req = UltravoxJoinRequest(
        language="es-ES",
        temperature=0.3,
        max_duration="1800s",
        recording_enabled=False,
        join_timeout="30s",
        initial_messages=[{"role": "user", "text": "Hello"}],
        initial_state={"step": "intro"},
    )
    assert req.temperature == 0.3
    assert req.max_duration == "1800s"
    assert req.recording_enabled is False
    assert req.join_timeout == "30s"
    assert req.initial_messages[0]["text"] == "Hello"
    assert req.initial_state["step"] == "intro"


def test_build_tool_overrides_data_connection():
    overrides = build_tool_overrides(["check_loan_emi"], implementation="dataConnection")
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
    agent.language = "en-US"
    greeting = resolve_call_greeting(agent, campaign_call_config={"greeting": "Campaign hi"})
    # Campaign greeting wins over the agent default; the AI-disclosure is prepended.
    assert "Campaign hi" in greeting
    assert "Agent hi" not in greeting


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
    from datetime import datetime, timezone

    secret = "test-secret"
    body = b'{"event":"call.ended","call":{"callId":"c1"}}'
    # Use a current timestamp so the 5-minute freshness check always passes.
    timestamp = datetime.now(timezone.utc).isoformat()
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
        "app.services.ultravox_webhook_service.session_manager.get_history",
        new_callable=AsyncMock,
        return_value=[],
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


def test_stage_definition_model():
    stage = StageDefinition(
        name="billing",
        system_prompt="You are a billing assistant.",
        voice="Jessica",
        temperature=0.3,
        language_hint="es-ES",
        tools=["get_order_status"],
    )
    assert stage.name == "billing"
    assert stage.voice == "Jessica"
    assert stage.temperature == 0.3


def test_get_agent_stages():
    agent = MagicMock()
    agent.config = {
        "stages": [
            {"name": "greeting", "system_prompt": "Say hello"},
            {"name": "billing", "system_prompt": "Handle billing", "temperature": 0.3},
        ]
    }
    stages = get_agent_stages(agent)
    assert len(stages) == 2
    assert stages[0].name == "greeting"
    assert stages[1].temperature == 0.3


def test_get_agent_stages_empty():
    agent = MagicMock()
    agent.config = {}
    assert get_agent_stages(agent) == []


def test_stage_change_tool_descriptor():
    desc = build_stage_change_tool_descriptor()
    assert desc["temporaryTool"]["modelToolName"] == STAGE_CHANGE_TOOL_NAME
    assert desc["temporaryTool"]["client"] == {}
    params = desc["temporaryTool"]["dynamicParameters"]
    assert any(p["name"] == "stage_name" for p in params)


def test_build_stage_response():
    stage = StageDefinition(
        name="billing",
        system_prompt="Billing mode",
        voice="Jessica",
        temperature=0.3,
        language_hint="es-ES",
        tools=["get_order_status"],
    )
    body = build_stage_response(stage)
    assert body["systemPrompt"] == "Billing mode"
    assert body["voice"] == "Jessica"
    assert body["temperature"] == 0.3
    assert body["languageHint"] == "es-ES"


def test_resolve_stage_config_with_override():
    agent = MagicMock()
    agent.config = {
        "stages": [
            {"name": "billing", "system_prompt": "Billing mode", "voice": "Jessica"}
        ]
    }
    config = resolve_stage_config(
        agent, "billing",
        current_system_prompt="Default prompt",
        current_voice="Mark",
        current_temperature=0.4,
        current_language="en-US",
    )
    assert config["systemPrompt"] == "Billing mode"
    assert config["voice"] == "Jessica"
    assert config["temperature"] == 0.4  # falls back to current
    assert config["languageHint"] == "en-US"  # falls back to current


def test_resolve_stage_config_unknown_falls_back():
    agent = MagicMock()
    agent.config = {"stages": [{"name": "billing", "system_prompt": "Billing"}]}
    config = resolve_stage_config(
        agent, "unknown",
        current_system_prompt="Default prompt",
        current_voice="Mark",
        current_temperature=0.4,
        current_language="en-US",
    )
    assert config["systemPrompt"] == "Default prompt"
