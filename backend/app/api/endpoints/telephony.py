"""
Telephony endpoints for Twilio inbound/outbound voice with Ultravox runtime support.
"""
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketState
from twilio.twiml.voice_response import VoiceResponse
from loguru import logger

from app.orchestration.ultravox_twilio import (
    ULTRAVOX_DATA_CONNECTION_CONTEXT,
    create_ultravox_twilio_call,
)
from app.orchestration.ultravox_events import (
    UltravoxTranscriptTracker,
    parse_tool_invocation,
    run_ultravox_tool,
)
from app.core import database
from app.core.config import settings
from app.models import agent as models
from app.orchestration.session_manager import session_manager
from app.services.monitoring_service import monitoring_service
from app.services.telephony_service import telephony_service
from app.services.tools.registry import AVAILABLE_TOOLS
from app.services.ultravox_service import UltravoxService

import json
import os
import random
import uuid

router = APIRouter()
ultravox_service = UltravoxService()

def _use_ultravox_runtime() -> bool:
    from app.orchestration.websocket_proxy import is_ultravox_runtime
    return is_ultravox_runtime()


def _server_host() -> str:
    return (settings.SERVER_HOST or os.getenv("SERVER_HOST", "localhost:8001")).strip()


def _ws_base_url() -> str:
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


def _https_base_url() -> str:
    host = _server_host()
    if host.startswith("http://") or host.startswith("https://"):
        return host.rstrip("/")
    return f"https://{host.rstrip('/')}"


def _twiml_say(message: str) -> str:
    response = VoiceResponse()
    response.say(message)
    return str(response)


def _extract_agent_tool_names(tools: Optional[List[Any]]) -> List[str]:
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


def _tool_json_schema_to_ultravox_dynamic_parameters(schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    properties = schema.get("properties") if isinstance(schema, dict) else {}
    required_names = set(schema.get("required") or []) if isinstance(schema, dict) else set()
    if not isinstance(properties, dict):
        return []

    dynamic_parameters: List[Dict[str, Any]] = []
    for param_name, param_schema in properties.items():
        safe_schema = (
            param_schema
            if isinstance(param_schema, dict)
            else {"type": "string", "description": f"Parameter {param_name}"}
        )
        dynamic_parameters.append(
            {
                "name": param_name,
                "location": "PARAMETER_LOCATION_BODY",
                "schema": safe_schema,
                "required": param_name in required_names,
            }
        )

    return dynamic_parameters


def _build_ultravox_selected_tools(
    tools: Optional[List[Any]],
    implementation: str = "dataConnection",
) -> List[Dict[str, Any]]:
    selected_tools: List[Dict[str, Any]] = []

    for tool_name in _extract_agent_tool_names(tools):
        tool = AVAILABLE_TOOLS.get(tool_name)
        if not tool:
            logger.warning(f"Skipping unknown tool '{tool_name}' for telephony Ultravox mapping")
            continue

        implementation_spec: Dict[str, Any]
        if implementation == "client":
            implementation_spec = {"client": {}}
        else:
            implementation_spec = {"dataConnection": {}}

        selected_tools.append(
            {
                "temporaryTool": {
                    "modelToolName": tool.name,
                    "description": tool.description,
                    "dynamicParameters": _tool_json_schema_to_ultravox_dynamic_parameters(
                        tool.parameters or {}
                    ),
                    **implementation_spec,
                }
            }
        )

    return selected_tools


def _resolve_active_agent_configuration(db: Session, agent: models.Agent) -> Dict[str, Any]:
    active_persona = agent.persona
    active_tools = agent.tools or []

    versions = db.query(models.AgentVersion).filter(
        models.AgentVersion.agent_id == agent.id,
        models.AgentVersion.weight > 0,
    ).all()
    if versions:
        total_weight = sum(v.weight for v in versions)
        if total_weight > 0:
            rand_val = random.randint(1, 100)
            cumulative = 0
            for version in versions:
                cumulative += version.weight
                if rand_val <= cumulative:
                    active_persona = version.persona
                    active_tools = version.tools
                    break
    elif agent.active_version_id:
        pinned_version = db.query(models.AgentVersion).filter(
            models.AgentVersion.id == agent.active_version_id
        ).first()
        if pinned_version:
            active_persona = pinned_version.persona
            active_tools = pinned_version.tools

    return {"persona": active_persona, "tools": active_tools}


async def _handle_inbound_voice_webhook(
    request: Request,
    db: Session,
    agent_id: Optional[str],
) -> Response:
    form_data = await request.form()
    twilio_call_sid = form_data.get("CallSid")
    called_number = form_data.get("To")
    caller_id = form_data.get("From")

    if agent_id:
        agent = db.query(models.Agent).filter(
            models.Agent.id == agent_id,
            models.Agent.is_active.is_(True),
        ).first()
    else:
        agent = db.query(models.Agent).filter(models.Agent.is_active.is_(True)).first()

    if not agent:
        logger.error("No active agent found for inbound Twilio call")
        return Response(
            content=_twiml_say("No assistant is configured for this number right now."),
            media_type="application/xml",
        )

    logger.info(
        f"Inbound Twilio call {twilio_call_sid} from {caller_id} to {called_number} for agent {agent.id}"
    )

    if _use_ultravox_runtime():
        try:
            created = await create_ultravox_twilio_call(
                db=db,
                agent=agent,
                call_direction="inbound",
                caller_id=caller_id,
                called_number=called_number,
                twilio_call_sid=twilio_call_sid,
            )
            join_url = created["call"].get("joinUrl")
            if not join_url:
                raise RuntimeError("Ultravox did not return joinUrl for inbound Twilio call")

            twiml = telephony_service.generate_twiml_stream(stream_url=join_url)
            return Response(content=twiml, media_type="application/xml")
        except Exception as exc:
            logger.error(f"Ultravox inbound Twilio setup failed: {exc}")

    legacy_stream_url = f"{_ws_base_url()}/api/v1/telephony/stream/{agent.id}"
    fallback_twiml = telephony_service.generate_twiml_stream(
        stream_url=legacy_stream_url,
        welcome_message=f"Hello, I am {agent.name}. How can I help you today?",
    )
    return Response(content=fallback_twiml, media_type="application/xml")


@router.post("/voice")
async def twilio_voice_webhook(
    request: Request,
    agent_id: Optional[str] = Query(default=None),
    db: Session = Depends(database.get_db),
):
    """Inbound Twilio voice webhook (optionally scoped by query param agent_id)."""
    return await _handle_inbound_voice_webhook(request, db, agent_id)


@router.post("/voice/{agent_id}")
async def twilio_voice_webhook_for_agent(
    agent_id: str,
    request: Request,
    db: Session = Depends(database.get_db),
):
    """Inbound Twilio voice webhook scoped by path agent_id."""
    return await _handle_inbound_voice_webhook(request, db, agent_id)


@router.websocket("/ultravox-data")
async def ultravox_data_connection(
    websocket: WebSocket,
    db: Session = Depends(database.get_db),
):
    """
    Data connection websocket consumed by Ultravox during Twilio calls.
    Handles tool execution and relays monitoring/compliance hooks.
    """
    await websocket.accept()

    token = websocket.query_params.get("token")
    if not token or token not in ULTRAVOX_DATA_CONNECTION_CONTEXT:
        await websocket.close(code=1008, reason="Invalid data connection token")
        return

    context = ULTRAVOX_DATA_CONNECTION_CONTEXT[token]
    session_id = context.get("session_id")
    agent_id = context.get("agent_id")
    org_id = context.get("organization_id")

    tracker = UltravoxTranscriptTracker(agent_id, org_id, state_name="ULTRAVOX_TWILIO")
    end_reason = "ultravox_data_connection_closed"

    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                event = json.loads(raw_message)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received on Ultravox data connection")
                continue

            event_type = event.get("type")

            if event_type == "call_started":
                call_id = event.get("callId")
                if call_id:
                    session_id = call_id
                    context["session_id"] = call_id
                continue

            if event_type == "transcript":
                await tracker.handle(event, session_id)
                continue

            if event_type == "state":
                if session_id:
                    await monitoring_service.broadcast_event(
                        session_id,
                        "ultravox_state",
                        {"state": event.get("state"), "provider": "twilio"},
                    )
                continue

            if event_type in {"data_connection_tool_invocation", "client_tool_invocation"}:
                tool_name, invocation_id, tool_arguments = parse_tool_invocation(event)
                result_message_type = (
                    "data_connection_tool_result"
                    if event_type == "data_connection_tool_invocation"
                    else "client_tool_result"
                )

                if session_id:
                    await monitoring_service.broadcast_event(
                        session_id,
                        "tool_call",
                        {"name": tool_name, "arguments": tool_arguments, "provider": "ultravox_twilio"},
                    )

                if not invocation_id:
                    logger.warning("Tool invocation missing invocationId on Ultravox data connection")
                    continue

                if not tool_name:
                    await websocket.send_json(
                        {
                            "type": result_message_type,
                            "invocationId": invocation_id,
                            "responseType": "tool-response",
                            "errorType": "undefined",
                            "errorMessage": "Tool name missing in invocation.",
                        }
                    )
                    continue

                payload, meta = await run_ultravox_tool(
                    tool_name=tool_name,
                    arguments=tool_arguments,
                    invocation_id=invocation_id,
                    db=db,
                    agent_id=agent_id,
                    session_id=session_id,
                    result_message_type=result_message_type,
                )
                await websocket.send_json(payload)
                if session_id:
                    await monitoring_service.broadcast_event(
                        session_id,
                        "tool_result",
                        {
                            "name": meta["name"],
                            "arguments": meta["arguments"],
                            "result": meta["result"],
                            "confidence": meta.get("confidence"),
                            "provider": "ultravox_twilio",
                            "error": meta["error"],
                        },
                    )
                continue

            if event_type == "call_event":
                if session_id:
                    await monitoring_service.broadcast_event(
                        session_id,
                        "ultravox_call_event",
                        event,
                    )

                call_event_name = str(
                    event.get("event")
                    or event.get("eventType")
                    or event.get("name")
                    or ""
                ).lower()
                if "end" in call_event_name:
                    end_reason = call_event_name
                    break
                continue
    except WebSocketDisconnect:
        logger.info("Ultravox Twilio data connection disconnected")
    except Exception as exc:
        logger.error(f"Ultravox Twilio data connection error: {exc}")
    finally:
        if session_id:
            try:
                await session_manager.end_session(session_id, end_reason)
            except Exception as end_error:
                logger.error(f"Failed to end telephony session {session_id}: {end_error}")

        ULTRAVOX_DATA_CONNECTION_CONTEXT.pop(token, None)

        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()


@router.websocket("/stream/{agent_id}")
async def twilio_media_stream(
    websocket: WebSocket,
    agent_id: str,
    db: Session = Depends(database.get_db),
):
    """
    Legacy Twilio media stream endpoint (non-Ultravox fallback path).
    """
    await websocket.accept()
    logger.info(f"Legacy Twilio media stream connected for agent {agent_id}")

    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        await websocket.close(code=4004, reason="Agent not found")
        return

    stream_sid = None
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)

            if data.get("event") == "start":
                stream_sid = data.get("start", {}).get("streamSid")
                logger.info(f"Legacy Twilio stream started: {stream_sid}")
                continue

            if data.get("event") == "stop":
                logger.info(f"Legacy Twilio stream stopped: {stream_sid}")
                break
    except WebSocketDisconnect:
        logger.info("Legacy Twilio media stream disconnected")
    except Exception as exc:
        logger.error(f"Legacy Twilio stream error: {exc}")
    finally:
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()


@router.post("/outbound")
async def make_outbound_call(
    to_number: str,
    agent_id: str,
    from_number: Optional[str] = None,
    db: Session = Depends(database.get_db),
):
    """Trigger an outbound call through Ultravox Twilio medium or legacy Twilio fallback."""
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        return {"status": "error", "error": "Agent not found"}

    # Pre-call limit check
    from app.services.usage_service import UsageService
    usage_svc = UsageService(db)
    call_check = usage_svc.check_call_allowed(agent.organization_id)
    if not call_check["allowed"]:
        reason = call_check.get("reason", "limit_exceeded")
        logger.warning(f"Call blocked for org {agent.organization_id}: {reason}")
        return {"status": "error", "error": f"Cannot initiate call — {reason.replace('_', ' ')}"}

    # India telephony compliance gate (DND / consent / calling hours / DLT)
    from app.services.call_compliance_service import CallComplianceService
    compliance = CallComplianceService(db)
    allowed, c_reason = compliance.check_call_allowed(
        to_number,
        organization_id=agent.organization_id,
        from_number=from_number or settings.TWILIO_PHONE_NUMBER,
    )
    if not allowed:
        logger.warning(f"Outbound call to {to_number} blocked by compliance: {c_reason}")
        return {"status": "error", "error": f"Call not permitted — {c_reason.replace('_', ' ')}"}

    if _use_ultravox_runtime():
        from_e164 = (
            from_number
            or settings.TWILIO_PHONE_NUMBER
            or os.getenv("TWILIO_FROM_NUMBER")
        )
        if not from_e164:
            return {
                "status": "error",
                "error": "Missing from_number and TWILIO_PHONE_NUMBER for Ultravox outbound Twilio call",
            }

        try:
            created = await create_ultravox_twilio_call(
                db=db,
                agent=agent,
                call_direction="outbound",
                caller_id=from_e164,
                called_number=to_number,
                twilio_call_sid=None,
                outgoing_to=to_number,
                outgoing_from=from_e164,
            )
            call = created["call"]
            return {
                "status": "initiated",
                "provider": "ultravox_twilio",
                "call_id": call.get("callId"),
                "join_url": call.get("joinUrl"),
            }
        except Exception as exc:
            logger.error(f"Ultravox outbound Twilio call setup failed: {exc}")
            return {"status": "error", "error": str(exc)}

    webhook_url = f"{_https_base_url()}/api/v1/telephony/voice/{agent_id}"
    from_e164 = from_number or os.getenv("TWILIO_FROM_NUMBER", "+15550001234")
    call_sid = await telephony_service.initiate_outbound_call(
        to_number=to_number,
        from_number=from_e164,
        webhook_url=webhook_url,
    )
    return {"status": "initiated", "provider": "twilio", "call_sid": call_sid}
