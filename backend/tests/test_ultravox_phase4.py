"""Ultravox Tier 4 — Deferred messages, HTTP tools, prior call inheritance, throttles, call listing."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestration.ultravox_call import (
    build_deferred_messages,
    build_per_call_overrides,
    check_call_throttle,
)
from app.schemas.orchestrator import DeferredMessage, UltravoxJoinRequest
from app.services.ultravox_service import UltravoxService


def test_deferred_message_schema():
    msg = DeferredMessage(message="We missed you!", delay="10m", medium="sms")
    assert msg.message == "We missed you!"
    assert msg.delay == "10m"
    assert msg.medium == "sms"


def test_deferred_message_defaults():
    msg = DeferredMessage(message="Hello")
    assert msg.delay == "5m"
    assert msg.medium == "sms"


def test_build_deferred_messages():
    result = build_deferred_messages([
        {"message": "We missed you!", "delay": "10m", "medium": "sms"},
        {"message": "Call us back", "delay": "1h", "medium": "sms"},
    ])
    assert result is not None
    assert len(result) == 2
    assert result[0]["message"] == "We missed you!"
    assert result[0]["delay"] == "10m"
    assert result[1]["medium"] == "sms"


def test_build_deferred_messages_empty():
    assert build_deferred_messages(None) is None
    assert build_deferred_messages([]) is None


def test_build_deferred_messages_minimal():
    result = build_deferred_messages([{"text": "Hello"}])
    assert result is not None
    assert result[0]["message"] == "Hello"
    assert result[0]["delay"] == "5m"


def test_deferred_messages_in_per_call_overrides():
    overrides = build_per_call_overrides(
        deferred_messages=[{"message": "Follow up", "delay": "1h", "medium": "sms"}],
    )
    assert "deferredMessages" in overrides
    assert overrides["deferredMessages"][0]["message"] == "Follow up"


def test_prior_call_id_in_per_call_overrides():
    overrides = build_per_call_overrides(prior_call_id="call-abc-123")
    assert overrides["priorCallId"] == "call-abc-123"


def test_prior_call_id_none_omitted():
    overrides = build_per_call_overrides()
    assert "priorCallId" not in overrides


def test_per_call_overrides_with_all_tier4():
    overrides = build_per_call_overrides(
        temperature=0.5,
        deferred_messages=[{"message": "Missed you", "medium": "sms"}],
        prior_call_id="prev-call-1",
    )
    assert overrides["temperature"] == 0.5
    assert overrides["deferredMessages"][0]["message"] == "Missed you"
    assert overrides["priorCallId"] == "prev-call-1"


def test_ultravox_join_request_with_tier4_fields():
    req = UltravoxJoinRequest(
        deferred_messages=[{"message": "Follow up", "delay": "30m", "medium": "sms"}],
        prior_call_id="call-xyz",
    )
    assert req.deferred_messages is not None
    assert req.deferred_messages[0]["message"] == "Follow up"
    assert req.prior_call_id == "call-xyz"


def test_ultravox_join_request_defaults():
    req = UltravoxJoinRequest()
    assert req.deferred_messages is None
    assert req.prior_call_id is None


@pytest.mark.asyncio
async def test_check_call_throttle_no_limit():
    mock_service = AsyncMock()
    mock_service.count_active_calls = AsyncMock(return_value=5)

    with patch("app.orchestration.ultravox_call.settings") as mock_settings:
        mock_settings.ULTRAVOX_MAX_CONCURRENT_CALLS = 0
        await check_call_throttle(mock_service)


@pytest.mark.asyncio
async def test_check_call_throttle_under_limit():
    mock_service = AsyncMock()
    mock_service.count_active_calls = AsyncMock(return_value=3)

    with patch("app.orchestration.ultravox_call.settings") as mock_settings:
        mock_settings.ULTRAVOX_MAX_CONCURRENT_CALLS = 10
        await check_call_throttle(mock_service)


@pytest.mark.asyncio
async def test_check_call_throttle_at_limit():
    mock_service = AsyncMock()
    mock_service.count_active_calls = AsyncMock(return_value=10)

    with patch("app.orchestration.ultravox_call.settings") as mock_settings:
        mock_settings.ULTRAVOX_MAX_CONCURRENT_CALLS = 10
        with pytest.raises(RuntimeError, match="Throttle limit reached"):
            await check_call_throttle(mock_service)


@pytest.mark.asyncio
async def test_check_call_throttle_over_limit():
    mock_service = AsyncMock()
    mock_service.count_active_calls = AsyncMock(return_value=15)

    with patch("app.orchestration.ultravox_call.settings") as mock_settings:
        mock_settings.ULTRAVOX_MAX_CONCURRENT_CALLS = 10
        with pytest.raises(RuntimeError, match="Throttle limit reached"):
            await check_call_throttle(mock_service)


def test_build_http_tool():
    from app.orchestration.ultravox_call import _build_http_tool
    result = _build_http_tool("get_order_status")
    assert result is None  # No http_config on tool


def test_build_http_tool_no_tool():
    from app.orchestration.ultravox_call import _build_http_tool
    result = _build_http_tool("nonexistent_tool")
    assert result is None


def test_selected_tools_with_http_implementation():
    from app.orchestration.ultravox_call import build_ultravox_selected_tools
    selected = build_ultravox_selected_tools(["get_order_status"], implementation="http")
    assert selected == []  # No http_config on tools


def test_selected_tools_with_http_falls_back_to_empty():
    from app.orchestration.ultravox_call import build_ultravox_selected_tools
    selected = build_ultravox_selected_tools([], implementation="http")
    assert selected == []


@pytest.mark.asyncio
async def test_ultravox_service_list_calls():
    service = UltravoxService(api_key="test-key", base_url="https://api.ultravox.ai/api")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"results": [{"callId": "c1", "state": "active"}]}

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.ultravox_service.httpx.AsyncClient", return_value=mock_client):
        calls = await service.list_calls(agent_id="agent-1", limit=10)

    assert len(calls) == 1
    assert calls[0]["callId"] == "c1"
    mock_client.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_ultravox_service_list_calls_not_enabled():
    with patch("app.services.ultravox_service.settings") as mock_settings:
        mock_settings.ULTRAVOX_API_KEY = None
        service = UltravoxService(api_key=None, base_url="https://api.ultravox.ai/api")
        calls = await service.list_calls()
        assert calls == []


@pytest.mark.asyncio
async def test_ultravox_service_count_active_calls():
    service = UltravoxService(api_key="test-key", base_url="https://api.ultravox.ai/api")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {"callId": "c1", "state": "active"},
            {"callId": "c2", "state": "completed"},
            {"callId": "c3", "state": "in_progress"},
        ]
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.ultravox_service.httpx.AsyncClient", return_value=mock_client):
        count = await service.count_active_calls()

    assert count == 2


@pytest.mark.asyncio
async def test_ultravox_service_count_active_calls_not_enabled():
    with patch("app.services.ultravox_service.settings") as mock_settings:
        mock_settings.ULTRAVOX_API_KEY = None
        service = UltravoxService(api_key=None, base_url="https://api.ultravox.ai/api")
        count = await service.count_active_calls()
        assert count == 0


@pytest.mark.asyncio
async def test_ultravox_service_count_active_calls_error():
    service = UltravoxService(api_key="test-key", base_url="https://api.ultravox.ai/api")

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=Exception("API error"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.ultravox_service.httpx.AsyncClient", return_value=mock_client):
        count = await service.count_active_calls()

    assert count == 0


def test_sync_module_imports_tier4():
    from app.services.ultravox_agent_sync import (
        start_ultravox_call_for_agent,
        start_ultravox_twilio_call_for_agent,
    )
    import inspect
    sig1 = inspect.signature(start_ultravox_call_for_agent)
    assert "deferred_messages" in sig1.parameters
    assert "prior_call_id" in sig1.parameters
    sig2 = inspect.signature(start_ultravox_twilio_call_for_agent)
    assert "deferred_messages" in sig2.parameters
    assert "prior_call_id" in sig2.parameters


def test_base_call_overrides_tier4_params():
    from app.services.ultravox_agent_sync import _base_call_overrides
    import inspect
    sig = inspect.signature(_base_call_overrides)
    assert "deferred_messages" in sig.parameters
    assert "prior_call_id" in sig.parameters
