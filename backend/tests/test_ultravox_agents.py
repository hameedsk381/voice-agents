"""Ultravox Agents Phase 1 — template sync and agent-scoped calls."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestration.ultravox_call import (
    build_call_template,
    build_template_context,
    build_twilio_call_overrides,
    get_ultravox_agent_id,
    merge_ultravox_config,
)
from app.services.ultravox_agent_sync import (
    delete_ultravox_agent_for_voise_agent,
    sync_agent_to_ultravox,
)
from app.services.ultravox_service import UltravoxService


def _fake_agent(**kwargs):
    agent = MagicMock()
    agent.id = kwargs.get("id", "voise-1")
    agent.name = kwargs.get("name", "Support Bot")
    agent.role = kwargs.get("role", "support")
    agent.persona = kwargs.get("persona", "You are helpful.")
    agent.language = kwargs.get("language", "en-US")
    agent.tools = kwargs.get("tools", [])
    agent.config = kwargs.get("config", {})
    return agent


def test_get_and_merge_ultravox_config():
    assert get_ultravox_agent_id(None) is None
    merged = merge_ultravox_config({"voice": "Mark"}, ultravox_agent_id="uv-99", synced_at="t")
    assert merged["ultravox_agent_id"] == "uv-99"
    assert merged["ultravox_synced_at"] == "t"
    assert merged["voice"] == "Mark"


def test_build_system_prompt_uses_template_language_variable():
    agent = _fake_agent()
    from app.orchestration.ultravox_call import build_system_prompt

    prompt = build_system_prompt(agent, "Hello", "en-US", use_template_variables=True)
    assert "{{language}}" in prompt
    assert "Respond only in {{language}}" in prompt


def test_build_twilio_call_overrides():
    overrides = build_twilio_call_overrides(
        "wss://api.example/ws?token=abc",
        outgoing_to="+15551111",
        outgoing_from="+15552222",
        language_hint="en-US",
    )
    assert overrides["medium"]["twilio"]["outgoing"]["to"] == "+15551111"
    assert overrides["dataConnection"]["websocketUrl"].startswith("wss://")
    assert overrides["languageHint"] == "en-US"


def test_build_inactivity_messages_defaults():
    from app.orchestration.ultravox_call import build_inactivity_messages
    messages = build_inactivity_messages()
    assert len(messages) == 2
    assert messages[0]["endBehaviour"] == "END_BEHAVIOR_UNSPECIFIED"
    assert messages[1]["endBehaviour"] == "END_BEHAVIOR_HANG_UP_SOFT"
    assert messages[1]["duration"] == "120s"


def test_build_inactivity_messages_custom():
    from app.orchestration.ultravox_call import build_inactivity_messages
    messages = build_inactivity_messages(
        timeout_seconds=60,
        warning_message="Hello?",
        final_message="Bye!",
    )
    assert len(messages) == 2
    assert messages[0]["message"] == "Hello?"
    assert messages[1]["message"] == "Bye!"
    assert messages[1]["duration"] == "60s"


def test_build_initial_messages():
    from app.orchestration.ultravox_call import build_initial_messages
    result = build_initial_messages([
        {"role": "user", "text": "Hi there"},
        {"role": "assistant", "text": "Hello! How can I help?"},
    ])
    assert result is not None
    assert len(result) == 2
    assert result[0]["role"] == "user"


def test_build_initial_messages_empty():
    from app.orchestration.ultravox_call import build_initial_messages
    assert build_initial_messages(None) is None
    assert build_initial_messages([]) is None


def test_build_per_call_overrides():
    from app.orchestration.ultravox_call import build_per_call_overrides
    overrides = build_per_call_overrides(
        temperature=0.7,
        max_duration="1800s",
        recording_enabled=False,
        join_timeout="30s",
        initial_messages=[{"role": "user", "text": "Hello"}],
        initial_state={"step": "greeting"},
    )
    assert overrides["temperature"] == 0.7
    assert overrides["maxDuration"] == "1800s"
    assert overrides["recordingEnabled"] is False
    assert overrides["joinTimeout"] == "30s"
    assert overrides["initialMessages"][0]["text"] == "Hello"
    assert overrides["initialState"]["step"] == "greeting"


def test_twilio_call_overrides_with_initial_state():
    from app.orchestration.ultravox_call import build_twilio_call_overrides
    overrides = build_twilio_call_overrides(
        "wss://ws.example",
        outgoing_to="+15551111",
        outgoing_from="+15552222",
        initial_state={"agent_id": "a1"},
    )
    assert overrides["initialState"]["agent_id"] == "a1"


def test_build_call_template_prompt_only():
    agent = _fake_agent(config={"greeting": "Hello from Voise AI"})
    template = build_call_template(
        agent,
        persona="Be concise.",
        voice="Mark",
        language="en-US",
    )
    assert "systemPrompt" in template
    assert template["voice"] == "Mark"
    assert "selectedTools" not in template
    assert "firstSpeakerSettings" not in template
    assert "inactivityMessages" in template
    assert len(template["inactivityMessages"]) == 2


def test_build_template_context():
    agent = _fake_agent()
    ctx = build_template_context(agent, caller_id="+15551234", language="es-ES")
    assert ctx["customerName"] == "+15551234"
    assert ctx["companyName"] == "Voise AI"
    assert ctx["language"] == "es-ES"


@pytest.mark.asyncio
async def test_sync_agent_creates_ultravox_agent():
    agent = _fake_agent()
    mock_service = AsyncMock()
    mock_service.create_agent.return_value = {"agentId": "uv-new"}

    with patch("app.services.ultravox_agent_sync.is_ultravox_runtime", return_value=True):
        uv_id = await sync_agent_to_ultravox(agent, ultravox=mock_service)

    assert uv_id == "uv-new"
    mock_service.create_agent.assert_awaited_once()
    mock_service.update_agent.assert_not_awaited()


@pytest.mark.asyncio
async def test_sync_agent_updates_existing():
    agent = _fake_agent(config={"ultravox_agent_id": "uv-existing"})
    mock_service = AsyncMock()

    with patch("app.services.ultravox_agent_sync.is_ultravox_runtime", return_value=True):
        uv_id = await sync_agent_to_ultravox(agent, ultravox=mock_service)

    assert uv_id == "uv-existing"
    mock_service.update_agent.assert_awaited_once()
    assert mock_service.update_agent.await_args.args[0] == "uv-existing"


@pytest.mark.asyncio
async def test_ultravox_service_create_agent_call():
    service = UltravoxService(api_key="test-key", base_url="https://api.ultravox.ai/api")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.content = b'{"joinUrl":"wss://x","callId":"c1"}'
    mock_response.json.return_value = {"joinUrl": "wss://x", "callId": "c1"}

    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.ultravox_service.httpx.AsyncClient", return_value=mock_client):
        result = await service.create_agent_call(
            "uv-1",
            template_context={"agentName": "Bot"},
            metadata={"agent_id": "a1"},
        )

    assert result["joinUrl"] == "wss://x"
    mock_client.request.assert_awaited_once()
    call_kwargs = mock_client.request.await_args.kwargs
    assert call_kwargs["json"]["templateContext"]["agentName"] == "Bot"


@pytest.mark.asyncio
async def test_delete_ultravox_agent_for_voise_agent():
    agent = _fake_agent(config={"ultravox_agent_id": "uv-del"})
    mock_service = AsyncMock()
    mock_service.delete_agent = AsyncMock()

    with patch("app.services.ultravox_agent_sync.is_ultravox_runtime", return_value=True):
        ok = await delete_ultravox_agent_for_voise_agent(agent, ultravox=mock_service)

    assert ok is True
    mock_service.delete_agent.assert_awaited_once_with("uv-del")
