"""Shared Ultravox call creation for browser (WebRTC) and server WebSocket proxy."""

from typing import Any, Dict, List, Optional

from app.models import agent as models
from app.services.tools.registry import AVAILABLE_TOOLS
from app.core.config import settings, ultravox_call_ended_webhook_url

CONFIG_KEY_ULTRAVOX_AGENT_ID = "ultravox_agent_id"
CONFIG_KEY_ULTRAVOX_SYNCED_AT = "ultravox_synced_at"

# Filled at call time via templateContext (Ultravox mustache templates).
ULTRAVOX_TEMPLATE_VARIABLES = [
    {"key": "agentName", "description": "Agent display name"},
    {"key": "companyName", "description": "Your organization (defaults to Voise AI)"},
    {"key": "customerName", "description": "Caller ID or customer name"},
    {"key": "language", "description": "BCP-47 language code for the call"},
    {"key": "role", "description": "Agent role or title"},
    {"key": "campaignName", "description": "Outbound campaign name"},
    {"key": "contactName", "description": "Campaign contact name"},
]


def extract_agent_tool_names(tools: Optional[List[Any]]) -> List[str]:
    names: List[str] = []
    seen = set()
    for tool in tools or []:
        tool_name: Optional[str] = None
        if isinstance(tool, str):
            tool_name = tool
        elif isinstance(tool, dict):
            tool_name = tool.get("name") or tool.get("tool_name") or tool.get("toolName")
        if isinstance(tool_name, str) and tool_name and tool_name not in seen:
            names.append(tool_name)
            seen.add(tool_name)
    return names


def tool_json_schema_to_ultravox_dynamic_parameters(schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    properties = schema.get("properties") if isinstance(schema, dict) else {}
    required_names = set(schema.get("required") or []) if isinstance(schema, dict) else set()
    if not isinstance(properties, dict):
        return []
    dynamic_parameters: List[Dict[str, Any]] = []
    for param_name, param_schema in properties.items():
        safe_schema = param_schema if isinstance(param_schema, dict) else {
            "type": "string",
            "description": f"Parameter {param_name}",
        }
        dynamic_parameters.append({
            "name": param_name,
            "location": "PARAMETER_LOCATION_BODY",
            "schema": safe_schema,
            "required": param_name in required_names,
        })
    return dynamic_parameters


def build_ultravox_selected_tools(
    tools: Optional[List[Any]],
    *,
    implementation: str = "client",
) -> List[Dict[str, Any]]:
    """
    Map local tool registry entries to Ultravox selectedTools.
    implementation: 'client' for ultravox-client SDK, 'dataConnection' for telephony WS.
    """
    selected: List[Dict[str, Any]] = []
    for tool_name in extract_agent_tool_names(tools):
        tool = AVAILABLE_TOOLS.get(tool_name)
        if not tool:
            continue
        temporary_tool: Dict[str, Any] = {
            "modelToolName": tool.name,
            "description": tool.description,
            "dynamicParameters": tool_json_schema_to_ultravox_dynamic_parameters(tool.parameters or {}),
        }
        if implementation == "dataConnection":
            temporary_tool["dataConnection"] = {}
        else:
            temporary_tool["client"] = {}
        selected.append({"temporaryTool": temporary_tool})
    return selected


def build_system_prompt(
    agent: models.Agent,
    active_persona: Optional[str],
    language: str,
    *,
    use_template_variables: bool = False,
) -> str:
    """
    When use_template_variables=True, language uses {{language}} for Ultravox Agents
    (resolved from templateContext at call time).
    """
    persona = active_persona or agent.persona
    if use_template_variables:
        return f"{persona}\n\nIMPORTANT: Respond only in " + "{{language}}."
    return f"{persona}\n\nIMPORTANT: Respond only in {language}."


def get_ultravox_agent_id(config: Optional[Dict[str, Any]]) -> Optional[str]:
    if not config:
        return None
    agent_id = config.get(CONFIG_KEY_ULTRAVOX_AGENT_ID)
    return str(agent_id) if agent_id else None


def merge_ultravox_config(
    config: Optional[Dict[str, Any]],
    *,
    ultravox_agent_id: str,
    synced_at: Optional[str] = None,
) -> Dict[str, Any]:
    merged = dict(config or {})
    merged[CONFIG_KEY_ULTRAVOX_AGENT_ID] = ultravox_agent_id
    if synced_at:
        merged[CONFIG_KEY_ULTRAVOX_SYNCED_AT] = synced_at
    return merged


def clear_ultravox_config(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    merged = dict(config or {})
    merged.pop(CONFIG_KEY_ULTRAVOX_AGENT_ID, None)
    merged.pop(CONFIG_KEY_ULTRAVOX_SYNCED_AT, None)
    return merged


def build_tool_overrides(
    tools: Optional[List[Any]],
    *,
    implementation: str = "client",
) -> Dict[str, Any]:
    """Per-call tool wiring — avoids flipping the shared agent template between channels."""
    selected = build_ultravox_selected_tools(tools, implementation=implementation)
    if not selected:
        return {}
    return {"toolOverrides": {"add": selected}}


def merge_call_overrides(*parts: Dict[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for part in parts:
        if part:
            merged.update(part)
    return merged


def build_first_speaker_override(greeting: Optional[str]) -> Optional[Dict[str, Any]]:
    if not greeting:
        return None
    return {"firstSpeakerSettings": {"agent": {"text": str(greeting)}}}


def resolve_call_greeting(
    agent: models.Agent,
    *,
    campaign_call_config: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Campaign greeting wins over agent default."""
    if campaign_call_config and campaign_call_config.get("greeting"):
        return str(campaign_call_config["greeting"])
    agent_greeting = (agent.config or {}).get("greeting")
    return str(agent_greeting) if agent_greeting else None


def build_call_callbacks() -> Optional[Dict[str, Any]]:
    """Lifecycle callbacks for call.ended → Voise AI webhook."""
    if not settings.ULTRAVOX_CALLBACKS_ENABLED:
        return None
    ended_url = ultravox_call_ended_webhook_url()
    if not ended_url:
        return None
    callback: Dict[str, Any] = {"url": ended_url}
    secret = settings.ULTRAVOX_CALLBACK_SECRET
    if secret:
        callback["secrets"] = [secret]
    return {"ended": callback}


def build_call_template(
    agent: models.Agent,
    *,
    persona: str,
    voice: str,
    language: str,
    temperature: float = 0.4,
    recording_enabled: bool = True,
) -> Dict[str, Any]:
    """Build Ultravox callTemplate — tools are applied per call via toolOverrides."""
    return {
        "systemPrompt": build_system_prompt(
            agent, persona, language, use_template_variables=True
        ),
        "voice": voice,
        "model": settings.ULTRAVOX_MODEL,
        "temperature": temperature,
        "recordingEnabled": recording_enabled,
        "initialOutputMedium": "MESSAGE_MEDIUM_VOICE",
        "languageHint": language,
    }


def build_template_context(
    agent: models.Agent,
    *,
    caller_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    language: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Variables for Ultravox systemPrompt {{placeholders}} at call time."""
    ctx: Dict[str, Any] = {
        "agentName": agent.name or "Assistant",
        "companyName": "Voise AI",
        "customerName": customer_name or caller_id or "there",
        "language": language or agent.language or "en-US",
        "role": agent.role or "assistant",
    }
    if extra:
        ctx.update({k: v for k, v in extra.items() if v is not None})
    return {k: str(v) for k, v in ctx.items()}


def build_twilio_call_overrides(
    data_connection_ws_url: str,
    *,
    outgoing_to: Optional[str] = None,
    outgoing_from: Optional[str] = None,
    language_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """Per-call overrides for POST /agents/{id}/calls (Twilio + data connection)."""
    payload: Dict[str, Any] = {
        "medium": {"twilio": {}},
        "dataConnection": {
            "websocketUrl": data_connection_ws_url,
            "dataMessages": {
                "callStarted": True,
                "transcript": True,
                "state": True,
                "dataConnectionToolInvocation": True,
                "callEvent": True,
            },
        },
    }
    if outgoing_to and outgoing_from:
        payload["medium"]["twilio"]["outgoing"] = {
            "to": outgoing_to,
            "from": outgoing_from,
        }
    if language_hint:
        payload["languageHint"] = language_hint
    return payload
