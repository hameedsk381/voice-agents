import asyncio
from sqlalchemy.orm import Session
from loguru import logger
from app.services.tools.registry import AVAILABLE_TOOLS
from app.services.tools.mcp_service import mcp_client
from app.services.hitl_service import HITLService
from app.orchestration.session_manager import session_manager

def validate_arguments(tool, arguments: dict) -> tuple[bool, str]:
    """Validate arguments against the tool's parameter schema (JSON Schema).
    Returns (is_valid, error_message).
    """
    params = tool.parameters or {}
    required = params.get("required", [])
    properties = params.get("properties", {})

    for req_field in required:
        if req_field not in arguments or arguments[req_field] is None:
            return False, f"Missing required argument: '{req_field}'"

    for arg_name, arg_value in arguments.items():
        if arg_name not in properties:
            return False, f"Unknown argument: '{arg_name}'"
        prop_schema = properties[arg_name]
        prop_type = prop_schema.get("type", "string")
        if prop_type == "string" and not isinstance(arg_value, str):
            return False, f"Argument '{arg_name}' must be a string"
        if prop_type == "number" and not isinstance(arg_value, (int, float)):
            return False, f"Argument '{arg_name}' must be a number"

    return True, ""


async def execute_tool(tool_name: str, arguments: dict, db: Session, agent_id: str, session_id: str = None) -> str:
    """Execute a tool and return the result.
    Includes precondition validation, HITL approval, and retry with exponential backoff.
    """
    if tool_name not in AVAILABLE_TOOLS:
        mcp_tools = await mcp_client.list_tools()
        if any(t["name"] == tool_name for t in mcp_tools):
            logger.info(f"Executing Tool '{tool_name}' via MCP Server")
            return await mcp_client.call_tool(tool_name, arguments)
        return f"Tool '{tool_name}' not found in local registry or MCP."

    tool = AVAILABLE_TOOLS[tool_name]

    # Precondition: Validate arguments against schema
    is_valid, error_msg = validate_arguments(tool, arguments)
    if not is_valid:
        logger.warning(f"Tool '{tool_name}' argument validation failed: {error_msg}")
        return f"Cannot execute '{tool_name}': {error_msg}"

    # Check if tool requires human approval
    if tool.requires_approval:
        hitl_service = HITLService(db)
        action = await hitl_service.create_pending_action(
            session_id=session_id,
            agent_id=agent_id,
            action_type=tool.name,
            description=f"Action requested by AI: {tool.name} with args {arguments}",
            payload=arguments
        )
        return f"The tool '{tool_name}' requires human authorization. I've submitted a request for approval (ID: {action.id[:8]}). I will continue once authorized."

    # Execution with Retry (2 passes with exponential backoff for transient errors)
    max_retries = 2
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            result = await tool.execute(**arguments)
            logger.info(f"Tool '{tool_name}' executed successfully (attempt {attempt}): {result}")

            if session_id:
                await session_manager.log_tool_call(session_id, tool_name, arguments, result)
            return result

        except (TimeoutError, ConnectionError, asyncio.TimeoutError) as e:
            last_exception = e
            if attempt < max_retries:
                backoff = 0.5 * (2 ** (attempt - 1))
                logger.warning(f"Tool '{tool_name}' transient error (attempt {attempt}/{max_retries}): {e}. Retrying in {backoff}s...")
                await asyncio.sleep(backoff)
            else:
                logger.error(f"Tool '{tool_name}' failed after {max_retries} attempts: {e}")
        except Exception as e:
            last_exception = e
            logger.error(f"Tool '{tool_name}' non-retryable error: {e}")
            break

    return f"Tool '{tool_name}' execution failed: {last_exception}"
