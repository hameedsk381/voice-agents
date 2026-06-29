import asyncio
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from loguru import logger
from app.services.tools.registry import AVAILABLE_TOOLS
from app.services.tools.base import ToolResult
from app.services.tools.mcp_service import mcp_client
from app.services.hitl_service import HITLService
from app.services.policy_service import PolicyService
from app.models.policy_rule import PolicyAction
from app.orchestration.session_manager import session_manager
from app.orchestration.tool_planner import get_tool_planner


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


async def plan_and_execute_tools(
    user_input: str,
    history: list,
    tool_schemas: list,
    db: Session,
    agent_id: str,
    session_id: str,
    available_tool_names: list = None,
) -> Tuple[Optional[str], list]:
    """
    Plan tool usage and execute tools in sequence.
    Returns (plan_statement, tool_results) where each tool_result is a dict
    with name, result, confidence, metadata.
    """
    planner = get_tool_planner()
    plan_statement, tool_calls = await planner.generate_plan(
        user_input, history, tool_schemas
    )

    if not tool_calls:
        return plan_statement, []

    tool_results = []
    for tc in tool_calls:
        name = tc.get("name")
        args = tc.get("arguments", {})
        if available_tool_names and name not in available_tool_names:
            continue
        result = await execute_tool(name, args, db, agent_id, session_id)
        tool_results.append(result)

    return plan_statement, tool_results


async def execute_tool(
    tool_name: str,
    arguments: dict,
    db: Session,
    agent_id: str,
    session_id: str = None,
) -> dict:
    """Execute a tool and return a result dict with result, confidence, metadata.
    Includes precondition validation, HITL approval, and retry with exponential backoff.
    Returns dict with keys: name, result (str), confidence (float), metadata (dict), error (bool).
    """
    if tool_name not in AVAILABLE_TOOLS:
        mcp_tools = await mcp_client.list_tools()
        if any(t["name"] == tool_name for t in mcp_tools):
            logger.info(f"Executing Tool '{tool_name}' via MCP Server")
            return {
                "name": tool_name,
                "result": await mcp_client.call_tool(tool_name, arguments),
                "confidence": 0.5,
                "metadata": {"source": "mcp"},
                "error": False,
            }
        return {
            "name": tool_name,
            "result": f"Tool '{tool_name}' not found in local registry or MCP.",
            "confidence": 1.0,
            "metadata": {},
            "error": True,
        }

    tool = AVAILABLE_TOOLS[tool_name]

    # Gate: simulated tools (fake/canned data) are refused unless explicitly enabled.
    from app.core.config import settings
    if getattr(tool, "simulated", False) and not settings.ALLOW_SIMULATED_TOOLS:
        logger.warning(f"Refused simulated tool '{tool_name}' (ALLOW_SIMULATED_TOOLS is False)")
        return {
            "name": tool_name,
            "result": f"The '{tool_name}' tool is not available — it returns simulated data and is disabled.",
            "confidence": 1.0,
            "metadata": {"simulated_tool_disabled": True},
            "error": True,
        }

    # Precondition: Validate arguments against schema
    is_valid, error_msg = validate_arguments(tool, arguments)
    if not is_valid:
        logger.warning(f"Tool '{tool_name}' argument validation failed: {error_msg}")
        return {
            "name": tool_name,
            "result": f"Cannot execute '{tool_name}': {error_msg}",
            "confidence": 1.0,
            "metadata": {},
            "error": True,
        }

    # 1. Pre-execution policy evaluation (DENY / ESCALATE / PERMIT)
    policy_service = PolicyService(db)
    policy_result = policy_service.evaluate(tool_name, arguments)
    logger.info(f"Policy evaluation for '{tool_name}': {policy_result.action} ({policy_result.reason})")

    if policy_result.action == PolicyAction.DENY.value:
        if session_id:
            await session_manager.log_tool_call(session_id, tool_name, arguments, f"DENIED: {policy_result.reason}")
        return {
            "name": tool_name,
            "result": f"I'm sorry, I cannot perform that action. {policy_result.reason}",
            "confidence": 1.0,
            "metadata": {"policy_action": "DENY", "reason": policy_result.reason},
            "error": True,
        }

    if policy_result.action == PolicyAction.ESCALATE.value:
        hitl_service = HITLService(db)
        action = await hitl_service.create_pending_action(
            session_id=session_id,
            agent_id=agent_id,
            action_type=tool.name,
            description=f"Action requested by AI: {tool.name} with args {arguments}",
            payload=arguments,
        )
        return {
            "name": tool_name,
            "result": f"The tool '{tool_name}' requires human authorization. I've submitted a request for approval (ID: {action.id[:8]}). I will continue once authorized.",
            "confidence": 0.5,
            "metadata": {"approval_id": action.id[:8]},
            "error": False,
        }

    # Backward-compatible fallback: tool-level requires_approval flag
    if policy_result.action == PolicyAction.PERMIT.value and getattr(tool, "requires_approval", False):
        hitl_service = HITLService(db)
        action = await hitl_service.create_pending_action(
            session_id=session_id,
            agent_id=agent_id,
            action_type=tool.name,
            description=f"Action requested by AI: {tool.name} with args {arguments}",
            payload=arguments,
        )
        return {
            "name": tool_name,
            "result": f"The tool '{tool_name}' requires human authorization. I've submitted a request for approval (ID: {action.id[:8]}). I will continue once authorized.",
            "confidence": 0.5,
            "metadata": {"approval_id": action.id[:8]},
            "error": False,
        }

    # Execution with Retry (2 passes with exponential backoff for transient errors)
    max_retries = 2
    last_exception = None

    # Context-aware tools (e.g. collections outcome tools) need DB + session access.
    exec_kwargs = dict(arguments)
    if getattr(tool, "needs_context", False):
        exec_kwargs["_db"] = db
        exec_kwargs["_session_id"] = session_id
        exec_kwargs["_agent_id"] = agent_id

    for attempt in range(1, max_retries + 1):
        try:
            tr: ToolResult = await tool.execute(**exec_kwargs)
            logger.info(
                f"Tool '{tool_name}' executed successfully (attempt {attempt}): "
                f"confidence={tr.confidence}, result={tr.result[:100] if tr.result else ''}"
            )

            result_dict = {
                "name": tool_name,
                "result": tr.result,
                "confidence": tr.confidence,
                "metadata": tr.metadata,
                "error": False,
            }

            if session_id:
                await session_manager.log_tool_call(
                    session_id, tool_name, arguments,
                    f"{tr.result} (conf={tr.confidence})",
                )
            return result_dict

        except (TimeoutError, ConnectionError, asyncio.TimeoutError) as e:
            last_exception = e
            if attempt < max_retries:
                backoff = 0.5 * (2 ** (attempt - 1))
                logger.warning(
                    f"Tool '{tool_name}' transient error (attempt {attempt}/{max_retries}): {e}. "
                    f"Retrying in {backoff}s..."
                )
                await asyncio.sleep(backoff)
            else:
                logger.error(f"Tool '{tool_name}' failed after {max_retries} attempts: {e}")
        except Exception as e:
            last_exception = e
            logger.error(f"Tool '{tool_name}' non-retryable error: {e}")
            break

    return {
        "name": tool_name,
        "result": f"Tool '{tool_name}' execution failed: {last_exception}",
        "confidence": 0.0,
        "metadata": {"error": str(last_exception)},
        "error": True,
    }
