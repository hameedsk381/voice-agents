import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.orchestration.session_manager import SessionManager


@pytest.mark.asyncio
async def test_set_and_get_floor_owner():
    manager = SessionManager()
    session = {
        "session_id": "s1",
        "agent_id": "a1",
        "metadata": {"channel": "websocket", "floor_owner": "user"},
        "history": [],
        "tool_calls": [],
    }

    with patch.object(manager, "connect", AsyncMock()), \
         patch.object(manager, "get_session", AsyncMock(return_value=session)), \
         patch.object(manager, "update_session", AsyncMock(return_value=session)) as mock_update:

        ok = await manager.set_floor_owner("s1", "agent")
        assert ok is True
        mock_update.assert_called_once()
        assert mock_update.call_args[0][1]["metadata"]["floor_owner"] == "agent"

        session["metadata"]["floor_owner"] = "agent"
        owner = await manager.get_floor_owner("s1")
        assert owner == "agent"
