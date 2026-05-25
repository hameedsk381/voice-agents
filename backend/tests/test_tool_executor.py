import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.orchestration.tool_executor import execute_tool, validate_arguments
from app.services.tools.base import BaseTool, ToolResult


class MockTool(BaseTool):
    name = "test_tool"
    description = "A test tool"
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "User name"},
            "age": {"type": "number", "description": "User age"}
        },
        "required": ["name"]
    }
    requires_approval = False

    async def execute(self, name: str, age: int = None) -> ToolResult:
        return ToolResult(result=f"Hello {name}, age {age}", confidence=0.95, metadata={"name": name})


class MockApprovalTool(BaseTool):
    name = "approval_tool"
    description = "Requires approval"
    parameters = {
        "type": "object",
        "properties": {
            "action": {"type": "string"}
        },
        "required": ["action"]
    }
    requires_approval = True

    async def execute(self, action: str) -> ToolResult:
        return ToolResult(result=f"Executed: {action}", confidence=0.9)


@pytest.fixture(autouse=True)
def mock_session_manager():
    with patch("app.orchestration.tool_executor.session_manager.log_tool_call", AsyncMock()) as mock:
        yield mock


@pytest.mark.asyncio
async def test_validate_arguments_valid():
    tool = MockTool()
    is_valid, msg = validate_arguments(tool, {"name": "Alice", "age": 30})
    assert is_valid
    assert msg == ""


@pytest.mark.asyncio
async def test_validate_arguments_missing_required():
    tool = MockTool()
    is_valid, msg = validate_arguments(tool, {"age": 30})
    assert not is_valid
    assert "Missing required" in msg


@pytest.mark.asyncio
async def test_validate_arguments_unknown_arg():
    tool = MockTool()
    is_valid, msg = validate_arguments(tool, {"name": "Alice", "extra": "bad"})
    assert not is_valid
    assert "Unknown argument" in msg


@pytest.mark.asyncio
async def test_validate_arguments_wrong_type():
    tool = MockTool()
    is_valid, msg = validate_arguments(tool, {"name": "Alice", "age": "thirty"})
    assert not is_valid
    assert "must be a number" in msg


@pytest.mark.asyncio
async def test_execute_tool_success():
    tool = MockTool()
    with patch("app.orchestration.tool_executor.AVAILABLE_TOOLS", {"test_tool": tool}), \
         patch("app.orchestration.tool_executor.mcp_client") as mock_mcp:
        mock_mcp.list_tools = AsyncMock(return_value=[])
        result = await execute_tool("test_tool", {"name": "Alice", "age": 30}, MagicMock(), "agent-1", "session-1")
        assert result["result"] == "Hello Alice, age 30"
        assert result["confidence"] == 0.95
        assert not result["error"]


@pytest.mark.asyncio
async def test_execute_tool_validation_failure():
    tool = MockTool()
    with patch("app.orchestration.tool_executor.AVAILABLE_TOOLS", {"test_tool": tool}), \
         patch("app.orchestration.tool_executor.mcp_client") as mock_mcp:
        mock_mcp.list_tools = AsyncMock(return_value=[])
        result = await execute_tool("test_tool", {}, MagicMock(), "agent-1", "session-1")
        assert "Missing required argument" in result["result"]
        assert result["error"]


@pytest.mark.asyncio
async def test_execute_tool_requires_approval():
    tool = MockApprovalTool()
    mock_hitl = MagicMock()
    mock_hitl.create_pending_action = AsyncMock(return_value=MagicMock(id="action-12345678"))

    with patch("app.orchestration.tool_executor.AVAILABLE_TOOLS", {"approval_tool": tool}), \
         patch("app.orchestration.tool_executor.mcp_client") as mock_mcp, \
         patch("app.orchestration.tool_executor.HITLService", return_value=mock_hitl):
        mock_mcp.list_tools = AsyncMock(return_value=[])
        result = await execute_tool("approval_tool", {"action": "refund"}, MagicMock(), "agent-1", "session-1")
        assert "requires human authorization" in result["result"]
        assert not result["error"]


@pytest.mark.asyncio
async def test_execute_tool_retry_and_succeed():
    """Tool that fails once on transient error, then succeeds on retry."""
    class RetryTool(BaseTool):
        name = "retry_tool"
        description = "Retry test"
        parameters = {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]}
        requires_approval = False
        def __init__(self):
            super().__init__()
            self.call_count = 0

        async def execute(self, x: str) -> ToolResult:
            self.call_count += 1
            if self.call_count == 1:
                raise TimeoutError("DB timeout")
            return ToolResult(result=f"Result: {x}", confidence=0.98)

    tool = RetryTool()
    with patch("app.orchestration.tool_executor.AVAILABLE_TOOLS", {"retry_tool": tool}), \
         patch("app.orchestration.tool_executor.mcp_client") as mock_mcp:
        mock_mcp.list_tools = AsyncMock(return_value=[])
        result = await execute_tool("retry_tool", {"x": "test"}, MagicMock(), "agent-1", "session-1")
        assert result["result"] == "Result: test"
        assert result["confidence"] == 0.98
        assert tool.call_count == 2


@pytest.mark.asyncio
async def test_execute_tool_retry_exhausted():
    class AlwaysFailsTool(BaseTool):
        name = "always_fails"
        description = "Always fails"
        parameters = {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]}
        requires_approval = False

        async def execute(self, x: str) -> ToolResult:
            raise ConnectionError("Connection refused")

    tool = AlwaysFailsTool()
    with patch("app.orchestration.tool_executor.AVAILABLE_TOOLS", {"always_fails": tool}), \
         patch("app.orchestration.tool_executor.mcp_client") as mock_mcp:
        mock_mcp.list_tools = AsyncMock(return_value=[])
        result = await execute_tool("always_fails", {"x": "test"}, MagicMock(), "agent-1", "session-1")
        assert "execution failed" in result["result"]
        assert result["error"]


@pytest.mark.asyncio
async def test_execute_tool_not_found():
    with patch("app.orchestration.tool_executor.AVAILABLE_TOOLS", {}), \
         patch("app.orchestration.tool_executor.mcp_client") as mock_mcp:
        mock_mcp.list_tools = AsyncMock(return_value=[])
        result = await execute_tool("nonexistent", {}, MagicMock(), "agent-1", "session-1")
        assert "not found" in result["result"]
        assert result["error"]
