"""
Sync Voise AI agents to Ultravox Agents (call templates).
https://docs.ultravox.ai/agents/overview
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config import settings
from app.models import agent as models
from app.orchestration.ultravox_call import (
    STAGE_CHANGE_TOOL_NAME,
    build_call_callbacks,
    build_call_template,
    build_first_speaker_override,
    build_per_call_overrides,
    build_shared_secrets,
    build_stage_change_tool_descriptor,
    build_tool_overrides,
    build_twilio_call_overrides,
    extract_agent_tool_names,
    get_agent_stages,
    get_ultravox_agent_id,
    merge_call_overrides,
    merge_ultravox_config,
)
from app.orchestration.websocket_proxy import is_ultravox_runtime
from app.services.ultravox_service import UltravoxService


def _resolve_voice(agent: models.Agent, voice_override: Optional[str] = None) -> str:
    agent_config = agent.config or {}
    voice = voice_override or agent_config.get("voice")
    if not voice or voice == "auto":
        return settings.ULTRAVOX_VOICE
    return voice


async def sync_agent_to_ultravox(
    agent: models.Agent,
    *,
    active_persona: Optional[str] = None,
    active_tools: Optional[List[Any]] = None,
    language: Optional[str] = None,
    voice: Optional[str] = None,
    ultravox: Optional[UltravoxService] = None,
) -> Optional[str]:
    """Create or update the Ultravox Agent template (prompt/voice only — tools per call)."""
    if not is_ultravox_runtime():
        return None

    service = ultravox or UltravoxService()
    persona = active_persona if active_persona is not None else agent.persona
    lang = language or agent.language or "en-US"
    selected_voice = _resolve_voice(agent, voice)

    has_stages = bool(get_agent_stages(agent))
    call_template = build_call_template(
        agent,
        persona=persona,
        voice=selected_voice,
        language=lang,
        include_stages=has_stages,
    )
    display_name = re.sub(r'[^a-zA-Z0-9_-]', '_', (agent.name or "Voise Agent"))[:64]
    existing_id = get_ultravox_agent_id(agent.config)

    try:
        if existing_id:
            await service.update_agent(
                existing_id,
                name=display_name,
                call_template=call_template,
            )
            ultravox_id = existing_id
            logger.info(f"Updated Ultravox agent {ultravox_id} for Voise agent {agent.id}")
        else:
            created = await service.create_agent(
                name=display_name,
                call_template=call_template,
            )
            ultravox_id = created.get("agentId")
            if not ultravox_id:
                raise RuntimeError("Ultravox create agent did not return agentId")
            logger.info(f"Created Ultravox agent {ultravox_id} for Voise agent {agent.id}")
    except Exception as exc:
        logger.error(f"Ultravox agent sync failed for {agent.id}: {exc}")
        raise

    return ultravox_id


async def delete_ultravox_agent_for_voise_agent(
    agent: models.Agent,
    *,
    ultravox: Optional[UltravoxService] = None,
) -> bool:
    """Best-effort delete of linked Ultravox Agent."""
    if not is_ultravox_runtime():
        return False
    uv_id = get_ultravox_agent_id(agent.config)
    if not uv_id:
        return False
    service = ultravox or UltravoxService()
    try:
        await service.delete_agent(uv_id)
        logger.info(f"Deleted Ultravox agent {uv_id} for Voise agent {agent.id}")
        return True
    except Exception as exc:
        logger.warning(f"Ultravox agent delete failed for {agent.id}: {exc}")
        return False


async def ensure_ultravox_agent_id(
    agent: models.Agent,
    db,
    *,
    active_persona: Optional[str] = None,
    language: Optional[str] = None,
    voice: Optional[str] = None,
) -> Optional[str]:
    """Return stored Ultravox agent id, always syncing to Ultravox to ensure freshness."""
    try:
        uv_id = await sync_agent_to_ultravox(
            agent,
            active_persona=active_persona,
            language=language,
            voice=voice,
        )
        if uv_id:
            agent.config = merge_ultravox_config(
                agent.config,
                ultravox_agent_id=uv_id,
                synced_at=datetime.now(timezone.utc).isoformat(),
            )
            db.commit()
            db.refresh(agent)
            return uv_id
    except Exception as exc:
        logger.warning(f"Failed to sync to Ultravox before call: {exc}")
        
    return get_ultravox_agent_id(agent.config)


def _base_call_overrides(
    tools: Optional[List[Any]] = None,
    *,
    tool_implementation: str,
    greeting: Optional[str] = None,
    agent: Optional[models.Agent] = None,
    temperature: Optional[float] = None,
    max_duration: Optional[str] = None,
    recording_enabled: Optional[bool] = None,
    join_timeout: Optional[str] = None,
    initial_messages: Optional[List[Dict[str, str]]] = None,
    initial_state: Optional[Dict[str, Any]] = None,
    retention_policy: Optional[str] = None,
    tools_remove: Optional[List[Any]] = None,
    tools_replace: Optional[List[Any]] = None,
    deferred_messages: Optional[List[Dict[str, Any]]] = None,
    prior_call_id: Optional[str] = None,
) -> Dict[str, Any]:
    effective_tools = list(tools) if tools else []
    has_stages = bool(agent and get_agent_stages(agent))
    if has_stages and STAGE_CHANGE_TOOL_NAME not in extract_agent_tool_names(effective_tools):
        effective_tools.append(STAGE_CHANGE_TOOL_NAME)

    parts: List[Dict[str, Any]] = [
        build_tool_overrides(
            effective_tools if tools is not None else None,
            implementation=tool_implementation,
            tools_remove=tools_remove,
            tools_replace=tools_replace,
        )
    ]
    callbacks = build_call_callbacks()
    if callbacks:
        parts.append({"callbacks": callbacks})
    greeting_override = build_first_speaker_override(greeting)
    if greeting_override:
        parts.append(greeting_override)
    per_call = build_per_call_overrides(
        temperature=temperature,
        max_duration=max_duration,
        recording_enabled=recording_enabled,
        join_timeout=join_timeout,
        initial_messages=initial_messages,
        initial_state=initial_state,
        retention_policy=retention_policy,
        deferred_messages=deferred_messages,
        prior_call_id=prior_call_id,
    )
    if per_call:
        parts.append(per_call)
    overrides = merge_call_overrides(*parts)
    secrets = build_shared_secrets()
    if secrets:
        overrides["sharedSecrets"] = secrets
    return overrides


async def start_ultravox_call_for_agent(
    agent: models.Agent,
    *,
    ultravox_agent_id: str,
    template_context: Dict[str, Any],
    metadata: Dict[str, Any],
    tools: Optional[List[Any]] = None,
    tool_implementation: str = "client",
    greeting: Optional[str] = None,
    extra_overrides: Optional[Dict[str, Any]] = None,
    ultravox: Optional[UltravoxService] = None,
    temperature: Optional[float] = None,
    max_duration: Optional[str] = None,
    recording_enabled: Optional[bool] = None,
    join_timeout: Optional[str] = None,
    initial_messages: Optional[List[Dict[str, str]]] = None,
    initial_state: Optional[Dict[str, Any]] = None,
    retention_policy: Optional[str] = None,
    tools_remove: Optional[List[Any]] = None,
    tools_replace: Optional[List[Any]] = None,
    deferred_messages: Optional[List[Dict[str, Any]]] = None,
    prior_call_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Start a call via POST /agents/{agentId}/calls."""
    service = ultravox or UltravoxService()
    overrides = _base_call_overrides(
        tools or agent.tools,
        tool_implementation=tool_implementation,
        greeting=greeting,
        agent=agent,
        temperature=temperature,
        max_duration=max_duration,
        recording_enabled=recording_enabled,
        join_timeout=join_timeout,
        initial_messages=initial_messages,
        initial_state=initial_state,
        retention_policy=retention_policy,
        tools_remove=tools_remove,
        tools_replace=tools_replace,
        deferred_messages=deferred_messages,
        prior_call_id=prior_call_id,
    )
    if extra_overrides:
        overrides = merge_call_overrides(overrides, extra_overrides)
    return await service.create_agent_call(
        ultravox_agent_id,
        template_context=template_context,
        metadata=metadata,
        call_overrides=overrides,
    )


async def start_ultravox_twilio_call_for_agent(
    agent: models.Agent,
    *,
    ultravox_agent_id: str,
    template_context: Dict[str, Any],
    metadata: Dict[str, Any],
    data_connection_ws_url: str,
    tools: Optional[List[Any]] = None,
    greeting: Optional[str] = None,
    outgoing_to: Optional[str] = None,
    outgoing_from: Optional[str] = None,
    ultravox: Optional[UltravoxService] = None,
    temperature: Optional[float] = None,
    max_duration: Optional[str] = None,
    recording_enabled: Optional[bool] = None,
    join_timeout: Optional[str] = None,
    initial_messages: Optional[List[Dict[str, str]]] = None,
    initial_state: Optional[Dict[str, Any]] = None,
    retention_policy: Optional[str] = None,
    tools_remove: Optional[List[Any]] = None,
    tools_replace: Optional[List[Any]] = None,
    deferred_messages: Optional[List[Dict[str, Any]]] = None,
    prior_call_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Start a Twilio + data-connection call from a synced Ultravox Agent."""
    twilio_overrides = build_twilio_call_overrides(
        data_connection_ws_url,
        outgoing_to=outgoing_to,
        outgoing_from=outgoing_from,
        language_hint=template_context.get("language"),
        initial_state=initial_state,
    )
    return await start_ultravox_call_for_agent(
        agent,
        ultravox_agent_id=ultravox_agent_id,
        template_context=template_context,
        metadata=metadata,
        tools=tools,
        tool_implementation="dataConnection",
        greeting=greeting,
        extra_overrides=twilio_overrides,
        ultravox=ultravox,
        temperature=temperature,
        max_duration=max_duration,
        recording_enabled=recording_enabled,
        join_timeout=join_timeout,
        initial_messages=initial_messages,
        initial_state=initial_state,
        retention_policy=retention_policy,
        tools_remove=tools_remove,
        tools_replace=tools_replace,
        deferred_messages=deferred_messages,
        prior_call_id=prior_call_id,
    )
