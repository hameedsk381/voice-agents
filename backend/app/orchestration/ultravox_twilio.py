"""
Ultravox + Twilio call session setup (inbound/outbound/campaign).
"""

import os
import uuid
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import agent as models
from app.models.campaign import Campaign, CampaignContact
from app.orchestration.agent_config import resolve_active_agent_config
from app.orchestration.session_manager import session_manager
from app.orchestration.ultravox_call import build_template_context, resolve_call_greeting
from app.services.monitoring_service import monitoring_service
from app.services.ultravox_agent_sync import (
    ensure_ultravox_agent_id,
    start_ultravox_twilio_call_for_agent,
)

# Ephemeral per-call context for Ultravox data-connection websocket callbacks.
ULTRAVOX_DATA_CONNECTION_CONTEXT: Dict[str, Dict[str, Any]] = {}


def _server_host() -> str:
    return (settings.SERVER_HOST or os.getenv("SERVER_HOST", "localhost:8001")).strip()


def ws_base_url() -> str:
    host = _server_host()
    if host.startswith("ws://") or host.startswith("wss://"):
        return host.rstrip("/")
    if host.startswith("http://"):
        return f"ws://{host[len('http://'):].rstrip('/')}"
    if host.startswith("https://"):
        return f"wss://{host[len('https://'):].rstrip('/')}"
    if "localhost" in host or host.startswith("127.0.0.1"):
        return f"ws://{host.rstrip('/')}"
    return f"wss://{host.rstrip('/')}"


def build_data_connection_url(token: str) -> str:
    query = urlencode({"token": token})
    return f"{ws_base_url()}/api/v1/telephony/ultravox-data?{query}"


async def create_ultravox_twilio_call(
    db: Session,
    agent: models.Agent,
    call_direction: str,
    caller_id: Optional[str],
    called_number: Optional[str],
    twilio_call_sid: Optional[str],
    outgoing_to: Optional[str] = None,
    outgoing_from: Optional[str] = None,
    campaign: Optional[Campaign] = None,
    campaign_contact: Optional[CampaignContact] = None,
) -> Dict[str, Any]:
    active_persona, active_tools, _ = resolve_active_agent_config(db, agent)
    session_language = agent.language or "en-US"
    token = str(uuid.uuid4())
    org_id = agent.organization_id
    call_config = (campaign.call_config or {}) if campaign else {}
    greeting = resolve_call_greeting(agent, campaign_call_config=call_config)
    temperature = call_config.get("temperature")
    max_duration = call_config.get("max_duration") or call_config.get("maxDuration")
    recording_enabled = call_config.get("recording_enabled") or call_config.get("recordingEnabled")
    join_timeout = call_config.get("join_timeout") or call_config.get("joinTimeout")
    initial_state = call_config.get("initial_state") or call_config.get("initialState")
    retention_policy = call_config.get("retention_policy") or call_config.get("retentionPolicy")
    tools_remove = call_config.get("tools_remove") or call_config.get("toolsRemove")
    tools_replace = call_config.get("tools_replace") or call_config.get("toolsReplace")
    deferred_messages = call_config.get("deferred_messages") or call_config.get("deferredMessages")
    prior_call_id = call_config.get("prior_call_id") or call_config.get("priorCallId")

    metadata: Dict[str, str] = {
        "agent_id": str(agent.id),
        "org_id": str(org_id) if org_id is not None else "",
        "channel": "twilio",
        "direction": call_direction,
    }
    if caller_id:
        metadata["caller_id"] = str(caller_id)
    if called_number:
        metadata["called_number"] = str(called_number)
    if twilio_call_sid:
        metadata["twilio_call_sid"] = str(twilio_call_sid)
    if campaign:
        metadata["campaign_id"] = str(campaign.id)
    if campaign_contact:
        metadata["campaign_contact_id"] = str(campaign_contact.id)

    ULTRAVOX_DATA_CONNECTION_CONTEXT[token] = {
        "token": token,
        "agent_id": agent.id,
        "organization_id": org_id,
        "caller_id": caller_id,
        "called_number": called_number,
        "twilio_call_sid": twilio_call_sid,
        "direction": call_direction,
        "campaign_id": campaign.id if campaign else None,
        "campaign_contact_id": campaign_contact.id if campaign_contact else None,
    }

    extra: Dict[str, Any] = {"direction": call_direction}
    if campaign:
        extra["campaignName"] = campaign.name
    if campaign_contact:
        extra["contactName"] = campaign_contact.contact_name or campaign_contact.phone_number
        for key, value in (campaign_contact.custom_data or {}).items():
            if value is not None:
                extra[key] = value

    template_context = build_template_context(
        agent,
        caller_id=caller_id,
        customer_name=campaign_contact.contact_name if campaign_contact else None,
        language=session_language,
        extra=extra,
    )

    try:
        ultravox_agent_id = await ensure_ultravox_agent_id(
            agent,
            db,
            active_persona=active_persona,
            language=session_language,
        )
        if not ultravox_agent_id:
            raise RuntimeError("Ultravox agent is not configured for telephony")

        call = await start_ultravox_twilio_call_for_agent(
            agent,
            ultravox_agent_id=ultravox_agent_id,
            template_context=template_context,
            metadata=metadata,
            data_connection_ws_url=build_data_connection_url(token),
            tools=active_tools or [],
            greeting=greeting,
            outgoing_to=outgoing_to,
            outgoing_from=outgoing_from,
            temperature=temperature,
            max_duration=max_duration,
            recording_enabled=recording_enabled,
            join_timeout=join_timeout,
            initial_state=initial_state,
            retention_policy=retention_policy,
            tools_remove=tools_remove,
            tools_replace=tools_replace,
            deferred_messages=deferred_messages,
            prior_call_id=prior_call_id,
        )
    except Exception:
        ULTRAVOX_DATA_CONNECTION_CONTEXT.pop(token, None)
        raise

    session_id = call.get("callId") or str(uuid.uuid4())
    ultravox_call_id = str(call.get("callId") or session_id)
    ULTRAVOX_DATA_CONNECTION_CONTEXT[token]["session_id"] = session_id

    session_metadata = {
        "channel": "twilio_ultravox",
        "org_id": org_id,
        "twilio_call_sid": twilio_call_sid,
        "called_number": called_number,
        "direction": call_direction,
        "ultravox_call_id": ultravox_call_id,
    }
    if campaign:
        session_metadata["campaign_id"] = campaign.id
    if campaign_contact:
        session_metadata["campaign_contact_id"] = campaign_contact.id

    await session_manager.create_session(
        session_id=session_id,
        agent_id=agent.id,
        caller_id=caller_id,
        metadata=session_metadata,
    )
    await session_manager.link_ultravox_call_id(session_id, ultravox_call_id)
    await monitoring_service.broadcast_event(
        session_id,
        "session_start",
        {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "caller_id": caller_id,
            "provider": "ultravox_twilio",
            "direction": call_direction,
            "campaign_id": campaign.id if campaign else None,
        },
    )

    logger.info(f"Ultravox Twilio call {ultravox_call_id} session {session_id}")
    return {"call": call, "token": token, "session_id": session_id}
