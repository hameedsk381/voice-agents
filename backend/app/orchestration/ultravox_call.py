"""Shared Ultravox call creation for browser (WebRTC) and server WebSocket proxy."""

from typing import Any, Dict, List, Optional

from app.models import agent as models
from app.services.tools.registry import AVAILABLE_TOOLS
from app.core.config import settings, ultravox_call_ended_webhook_url
from app.core.languages import language_name, default_language
from app.schemas.orchestrator import InactivityMessage, StageDefinition

CONFIG_KEY_ULTRAVOX_AGENT_ID = "ultravox_agent_id"
CONFIG_KEY_ULTRAVOX_SYNCED_AT = "ultravox_synced_at"

STAGE_CHANGE_TOOL_NAME = "change_stage"

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


def _build_temporary_tool(
    tool_name: str,
    implementation: str,
) -> Optional[Dict[str, Any]]:
    tool = AVAILABLE_TOOLS.get(tool_name)
    if not tool:
        return None
    temporary: Dict[str, Any] = {
        "modelToolName": tool.name,
        "description": tool.description,
        "dynamicParameters": tool_json_schema_to_ultravox_dynamic_parameters(tool.parameters or {}),
    }
    if implementation == "dataConnection":
        temporary["dataConnection"] = {}
    else:
        temporary["client"] = {}
    return {"temporaryTool": temporary}


def build_ultravox_selected_tools(
    tools: Optional[List[Any]],
    *,
    implementation: str = "client",
) -> List[Dict[str, Any]]:
    """
    Map local tool registry entries to Ultravox selectedTools (for add operations).
    implementation: 'client' for ultravox-client SDK, 'dataConnection' for telephony WS, 'http' for server-side HTTP tools.
    """
    selected: List[Dict[str, Any]] = []
    for tool_name in extract_agent_tool_names(tools):
        if implementation == "http":
            entry = _build_http_tool(tool_name)
        else:
            entry = _build_temporary_tool(tool_name, implementation)
        if entry:
            selected.append(entry)
    return selected


def _build_http_tool(tool_name: str) -> Optional[Dict[str, Any]]:
    """Build an HTTP tool descriptor for server-side tool execution via Ultravox."""
    tool = AVAILABLE_TOOLS.get(tool_name)
    if not tool:
        return None
    http_config = getattr(tool, "http_config", None)
    if not http_config:
        return None
    return {
        "temporaryTool": {
            "modelToolName": tool.name,
            "description": tool.description,
            "http": {
                "baseUrlPattern": http_config.get("baseUrlPattern", ""),
                "httpMethod": http_config.get("httpMethod", "POST"),
            },
            "dynamicParameters": tool_json_schema_to_ultravox_dynamic_parameters(tool.parameters or {}),
        }
    }


def build_ultravox_tool_names_list(tools: Optional[List[Any]]) -> List[str]:
    """Build a list of tool names for toolOverrides remove operations."""
    return extract_agent_tool_names(tools)


def _language_label(code: str) -> str:
    return language_name(code)


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
    label = "{{language}}" if use_template_variables else _language_label(language)
    return f"{persona}\n\nIMPORTANT: Respond only in {label}."


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
    tools: Optional[List[Any]] = None,
    *,
    implementation: str = "client",
    tools_remove: Optional[List[Any]] = None,
    tools_replace: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """
    Per-call tool wiring.
    tools: tools to add.
    tools_remove: tool names/refs to remove from the agent's base tool set.
    tools_replace: if set, replaces the entire tool list (add + remove are ignored).
    """
    overrides: Dict[str, Any] = {}

    if tools_replace is not None:
        replaced = build_ultravox_selected_tools(tools_replace, implementation=implementation)
        if replaced:
            overrides["replace"] = replaced
        return {"toolOverrides": overrides} if overrides else {}

    if tools_remove is not None:
        removed = build_ultravox_tool_names_list(tools_remove)
        if removed:
            overrides["remove"] = removed

    if tools is not None:
        added = build_ultravox_selected_tools(tools, implementation=implementation)
        if added:
            overrides["add"] = added

    return {"toolOverrides": overrides} if overrides else {}


def merge_call_overrides(*parts: Dict[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for part in parts:
        if part:
            merged.update(part)
    return merged


def get_agent_stages(agent: models.Agent) -> List[StageDefinition]:
    """Read stage definitions from agent config."""
    raw = (agent.config or {}).get("stages") or []
    if isinstance(raw, list):
        return [StageDefinition(**s) if isinstance(s, dict) else s for s in raw if isinstance(s, (dict, StageDefinition))]
    return []


def get_agent_stage_names(agent: models.Agent) -> List[str]:
    """Get the list of stage names defined for an agent."""
    return [s.name for s in get_agent_stages(agent)]


def build_stage_change_tool_descriptor() -> Dict[str, Any]:
    """Build a temporaryTool descriptor for the built-in change_stage tool."""
    return {
        "temporaryTool": {
            "modelToolName": STAGE_CHANGE_TOOL_NAME,
            "description": "Transition the conversation to a named stage. Available stages are listed in the system prompt.",
            "client": {},
            "dynamicParameters": [
                {
                    "name": "stage_name",
                    "location": "PARAMETER_LOCATION_BODY",
                    "schema": {"type": "string", "description": "The name of the stage to transition to"},
                    "required": True,
                }
            ],
        }
    }


def build_stage_change_prompt_instruction(agent: models.Agent) -> str:
    """Generate a system prompt instruction about available stages."""
    stages = get_agent_stages(agent)
    if not stages:
        return ""
    names = [s.name for s in stages]
    lines = [
        "\n\nYou can transition between conversation stages using the change_stage tool.",
        f"Available stages: {', '.join(names)}.",
        "When the topic or context shifts, use change_stage to switch to the appropriate stage.",
    ]
    for s in stages:
        desc = s.system_prompt or s.name
        lines.append(f"- '{s.name}': {desc[:100]}")
    return "\n".join(lines)


def build_stage_response(
    stage: StageDefinition,
) -> Dict[str, Any]:
    """Build a stage-change tool result for the given stage definition.
    Callers should wrap this with build_tool_result(response_type="new-stage")."""
    body: Dict[str, Any] = {}
    if stage.system_prompt:
        body["systemPrompt"] = stage.system_prompt
    if stage.voice:
        body["voice"] = stage.voice
    if stage.temperature is not None:
        body["temperature"] = stage.temperature
    if stage.language_hint:
        body["languageHint"] = stage.language_hint
    if stage.tools:
        tool_entries = []
        for name in stage.tools:
            entry = _build_temporary_tool(name, "client")
            if entry:
                tool_entries.append(entry)
        if tool_entries:
            body["selectedTools"] = tool_entries
    return body


def resolve_stage_config(
    agent: models.Agent,
    stage_name: str,
    current_system_prompt: str,
    current_voice: str,
    current_temperature: float,
    current_language: str,
) -> Dict[str, Any]:
    """Resolve a named stage to its full config, falling back to current values for unspecified fields."""
    stages = get_agent_stages(agent)
    stage = next((s for s in stages if s.name == stage_name), None)
    if not stage:
        return {"systemPrompt": current_system_prompt}
    body = build_stage_response(stage)
    if "systemPrompt" not in body:
        body["systemPrompt"] = current_system_prompt
    if "voice" not in body:
        body["voice"] = current_voice
    if "temperature" not in body:
        body["temperature"] = current_temperature
    if "languageHint" not in body:
        body["languageHint"] = current_language
    return body


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


def build_inactivity_messages(
    timeout_seconds: Optional[int] = None,
    warning_message: Optional[str] = None,
    final_message: Optional[str] = None,
) -> List[Dict[str, Any]]:
    timeout = timeout_seconds or settings.ULTRAVOX_INACTIVITY_TIMEOUT_SECONDS
    messages: List[Dict[str, Any]] = []
    warning = warning_message or settings.ULTRAVOX_INACTIVITY_WARNING_MESSAGE
    if warning:
        messages.append({
            "message": str(warning),
            "duration": str(max(timeout // 2, 30)) + "s",
            "endBehavior": "END_BEHAVIOR_UNSPECIFIED",
        })
    final = final_message or settings.ULTRAVOX_INACTIVITY_FINAL_MESSAGE
    if final:
        messages.append({
            "message": str(final),
            "duration": str(timeout) + "s",
            "endBehavior": "END_BEHAVIOR_HANG_UP_SOFT",
        })
    return messages


def build_tool_result(
    result: Dict[str, Any],
    *,
    response_type: Optional[str] = None,
    agent_reaction: Optional[str] = None,
    call_state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Wrap a tool result with Ultravox guidance fields.
    Tool implementors can call this to guide agent behavior after a tool runs.
    - response_type: "tool-response" (default), "new-stage", "push"
    - agent_reaction: "speaks-once", "speaks-never", "speaks-and-listens"
    - call_state: dict to persist as tool state between invocations
    """
    wrapped = dict(result)
    if response_type:
        wrapped["_response_type"] = response_type
    if agent_reaction:
        wrapped["_agent_reaction"] = agent_reaction
    if call_state is not None:
        wrapped["_call_state"] = call_state
    return wrapped


def build_shared_secrets() -> Optional[List[str]]:
    if not settings.ULTRAVOX_SHARED_SECRETS:
        return None
    secrets = [s.strip() for s in settings.ULTRAVOX_SHARED_SECRETS.split(",") if s.strip()]
    return secrets if secrets else None


def build_retention_policy(policy: Optional[str] = None) -> Optional[str]:
    p = policy or settings.ULTRAVOX_RETENTION_POLICY
    valid = {"CALL_RETENTION_POLICY_RETAIN", "CALL_RETENTION_POLICY_AUTO_DELETE", "CALL_RETENTION_POLICY_UNSPECIFIED"}
    return p if p in valid else None


def build_initial_messages(
    messages: Optional[List[Dict[str, str]]],
) -> Optional[List[Dict[str, str]]]:
    if not messages:
        return None
    cleaned: List[Dict[str, str]] = []
    for msg in messages:
        role = msg.get("role", "user")
        text = msg.get("text") or msg.get("content") or ""
        if text:
            cleaned.append({"role": role, "text": str(text)})
    return cleaned or None


async def check_call_throttle(ultravox_service) -> None:
    """Raise RuntimeError if at or above the max concurrent calls limit."""
    max_calls = settings.ULTRAVOX_MAX_CONCURRENT_CALLS
    if max_calls <= 0:
        return
    active = await ultravox_service.count_active_calls()
    if active >= max_calls:
        raise RuntimeError(
            f"Throttle limit reached: {active} active calls, max {max_calls}. "
            "Please wait for an existing call to end."
        )


def build_deferred_messages(
    messages: Optional[List[Dict[str, Any]]] = None,
) -> Optional[List[Dict[str, Any]]]:
    """Build deferredMessages payload for post-call follow-up messages."""
    if not messages:
        return None
    cleaned: List[Dict[str, Any]] = []
    for msg in messages:
        text = msg.get("message") or msg.get("text", "")
        delay = msg.get("delay", "5m")
        medium = msg.get("medium", "sms")
        if text:
            cleaned.append({"message": str(text), "delay": str(delay), "medium": str(medium)})
    return cleaned or None


def build_per_call_overrides(
    *,
    temperature: Optional[float] = None,
    max_duration: Optional[str] = None,
    recording_enabled: Optional[bool] = None,
    join_timeout: Optional[str] = None,
    initial_messages: Optional[List[Dict[str, str]]] = None,
    initial_state: Optional[Dict[str, Any]] = None,
    retention_policy: Optional[str] = None,
    deferred_messages: Optional[List[Dict[str, Any]]] = None,
    prior_call_id: Optional[str] = None,
) -> Dict[str, Any]:
    overrides: Dict[str, Any] = {}
    if temperature is not None:
        overrides["temperature"] = temperature
    if max_duration is not None:
        overrides["maxDuration"] = max_duration
    resolved_recording = recording_enabled if recording_enabled is not None else settings.ULTRAVOX_DEFAULT_RECORDING_ENABLED
    overrides["recordingEnabled"] = resolved_recording
    if join_timeout is not None:
        overrides["joinTimeout"] = join_timeout
    initial_msgs = build_initial_messages(initial_messages)
    if initial_msgs:
        overrides["initialMessages"] = initial_msgs
    if initial_state is not None:
        overrides["initialState"] = initial_state
    rp = build_retention_policy(retention_policy)
    if rp:
        overrides["retentionPolicy"] = rp
    deferred = build_deferred_messages(deferred_messages)
    if deferred:
        overrides["deferredMessages"] = deferred
    if prior_call_id is not None:
        overrides["priorCallId"] = prior_call_id
    return overrides


def build_call_template(
    agent: models.Agent,
    *,
    persona: str,
    voice: str,
    language: str,
    temperature: float = 0.4,
    recording_enabled: Optional[bool] = None,
    inactivity_timeout_seconds: Optional[int] = None,
    inactivity_warning: Optional[str] = None,
    inactivity_final: Optional[str] = None,
    include_stages: bool = False,
) -> Dict[str, Any]:
    """Build Ultravox callTemplate — tools are applied per call via toolOverrides."""
    system_prompt = build_system_prompt(
        agent, persona, language, use_template_variables=True
    )
    if include_stages:
        stage_instruction = build_stage_change_prompt_instruction(agent)
        if stage_instruction:
            system_prompt += stage_instruction

    template: Dict[str, Any] = {
        "systemPrompt": system_prompt,
        "voice": voice,
        "model": settings.ULTRAVOX_MODEL,
        "temperature": temperature,
        "recordingEnabled": recording_enabled if recording_enabled is not None else settings.ULTRAVOX_DEFAULT_RECORDING_ENABLED,
        "initialOutputMedium": "MESSAGE_MEDIUM_VOICE",
        "languageHint": language,
    }
    inactivity_messages = build_inactivity_messages(
        timeout_seconds=inactivity_timeout_seconds,
        warning_message=inactivity_warning,
        final_message=inactivity_final,
    )
    if inactivity_messages:
        template["inactivityMessages"] = inactivity_messages
    return template


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
        "language": _language_label(language or agent.language or "en-US"),
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
    initial_state: Optional[Dict[str, Any]] = None,
    shared_secrets: Optional[List[str]] = None,
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
    if initial_state is not None:
        payload["initialState"] = initial_state
    secrets = shared_secrets or build_shared_secrets()
    if secrets:
        payload["sharedSecrets"] = secrets
    return payload
