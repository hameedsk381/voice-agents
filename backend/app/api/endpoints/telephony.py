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

from app.api.endpoints.orchestrator import execute_tool, _run_ultravox_compliance_audit
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

# Ephemeral per-call context used by Ultravox data connection websocket callbacks.
_ULTRAVOX_DATA_CONNECTION_CONTEXT: Dict[str, Dict[str, Any]] = {}


def _use_ultravox_runtime() -> bool:
    return settings.USE_ULTRAVOX_RUNTIME and ultravox_service.enabled


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


def _build_data_connection_url(token: str) -> str:
    query = urlencode({"token": token})
    return f"{_ws_base_url()}/api/v1/telephony/ultravox-data?{query}"


async def _create_ultravox_twilio_call(
    db: Session,
    agent: models.Agent,
    call_direction: str,
    caller_id: Optional[str],
    called_number: Optional[str],
    twilio_call_sid: Optional[str],
    outgoing_to: Optional[str] = None,
    outgoing_from: Optional[str] = None,
) -> Dict[str, Any]:
    active_config = _resolve_active_agent_configuration(db, agent)
    session_language = agent.language or "en-US"
    token = str(uuid.uuid4())
    org_id = agent.organization_id

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

    call_payload: Dict[str, Any] = {
        "systemPrompt": f"{active_config['persona']}\n\nIMPORTANT: Respond only in {session_language}.",
        "model": settings.ULTRAVOX_MODEL,
        "voice": settings.ULTRAVOX_VOICE,
        "languageHint": session_language,
        "selectedTools": _build_ultravox_selected_tools(active_config["tools"], implementation="dataConnection"),
        "metadata": metadata,
        "initialState": {
            "agent_id": str(agent.id),
            "organization_id": str(org_id) if org_id is not None else "",
            "direction": call_direction,
        },
        "medium": {"twilio": {}},
        "dataConnection": {
            "websocketUrl": _build_data_connection_url(token),
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
        call_payload["medium"]["twilio"]["outgoing"] = {
            "to": outgoing_to,
            "from": outgoing_from,
        }

    _ULTRAVOX_DATA_CONNECTION_CONTEXT[token] = {
        "token": token,
        "agent_id": agent.id,
        "organization_id": org_id,
        "caller_id": caller_id,
        "called_number": called_number,
        "twilio_call_sid": twilio_call_sid,
        "direction": call_direction,
    }

    try:
        call = await ultravox_service.create_call(call_payload)
    except Exception:
        _ULTRAVOX_DATA_CONNECTION_CONTEXT.pop(token, None)
        raise

    session_id = call.get("callId") or str(uuid.uuid4())
    _ULTRAVOX_DATA_CONNECTION_CONTEXT[token]["session_id"] = session_id

    await session_manager.create_session(
        session_id=session_id,
        agent_id=agent.id,
        caller_id=caller_id,
        metadata={
            "channel": "twilio_ultravox",
            "org_id": org_id,
            "twilio_call_sid": twilio_call_sid,
            "called_number": called_number,
            "direction": call_direction,
        },
    )
    await monitoring_service.broadcast_event(
        session_id,
        "session_start",
        {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "caller_id": caller_id,
            "provider": "ultravox_twilio",
            "direction": call_direction,
        },
    )

    return {"call": call, "token": token, "session_id": session_id}


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
            created = await _create_ultravox_twilio_call(
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
    if not token or token not in _ULTRAVOX_DATA_CONNECTION_CONTEXT:
        await websocket.close(code=1008, reason="Invalid data connection token")
        return

    context = _ULTRAVOX_DATA_CONNECTION_CONTEXT[token]
    session_id = context.get("session_id")
    agent_id = context.get("agent_id")
    org_id = context.get("organization_id")

    transcript_buffers: Dict[tuple, str] = {}
    unanswered_user_turns: List[str] = []
    turn_count = 0
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
                role = event.get("role", "agent")
                ordinal = int(event.get("ordinal") or 0)
                key = (role, ordinal)

                delta = event.get("delta") or ""
                full_text = event.get("text")
                is_final = bool(event.get("final"))

                if full_text is not None:
                    transcript_buffers[key] = full_text
                elif delta:
                    transcript_buffers[key] = transcript_buffers.get(key, "") + delta

                if is_final and session_id:
                    final_text = transcript_buffers.pop(key, full_text or delta).strip()
                    if final_text:
                        mapped_role = "assistant" if role == "agent" else "user"
                        await session_manager.add_to_history(session_id, mapped_role, final_text)
                        await monitoring_service.broadcast_event(
                            session_id,
                            "transcription",
                            {"text": final_text, "role": mapped_role},
                        )

                        if mapped_role == "user":
                            unanswered_user_turns.append(final_text)
                        elif unanswered_user_turns and agent_id:
                            user_turn_for_audit = unanswered_user_turns.pop(0)
                            turn_count += 1
                            try:
                                await _run_ultravox_compliance_audit(
                                    db=db,
                                    session_id=session_id,
                                    agent_id=agent_id,
                                    organization_id=org_id,
                                    turn_index=turn_count,
                                    user_input=user_turn_for_audit,
                                    ai_response=final_text,
                                    state_name="ULTRAVOX_TWILIO",
                                )
                            except Exception as audit_error:
                                logger.error(f"Ultravox Twilio compliance audit failed: {audit_error}")
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
                tool_name = event.get("toolName") or event.get("name")
                invocation_id = event.get("invocationId") or event.get("id")
                tool_arguments = event.get("parameters") or {}
                if not isinstance(tool_arguments, dict):
                    tool_arguments = {}

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

                try:
                    result = await execute_tool(
                        tool_name=tool_name,
                        arguments=tool_arguments,
                        db=db,
                        agent_id=agent_id,
                        session_id=session_id,
                    )
                    await websocket.send_json(
                        {
                            "type": result_message_type,
                            "invocationId": invocation_id,
                            "result": result,
                            "responseType": "tool-response",
                        }
                    )

                    if session_id:
                        await monitoring_service.broadcast_event(
                            session_id,
                            "tool_result",
                            {
                                "name": tool_name,
                                "arguments": tool_arguments,
                                "result": result,
                                "provider": "ultravox_twilio",
                            },
                        )
                except Exception as tool_error:
                    logger.error(f"Ultravox Twilio tool execution failed ({tool_name}): {tool_error}")
                    await websocket.send_json(
                        {
                            "type": result_message_type,
                            "invocationId": invocation_id,
                            "responseType": "tool-response",
                            "errorType": "implementation-error",
                            "errorMessage": str(tool_error),
                        }
                    )
                    if session_id:
                        await monitoring_service.broadcast_event(
                            session_id,
                            "tool_result",
                            {
                                "name": tool_name,
                                "arguments": tool_arguments,
                                "result": str(tool_error),
                                "provider": "ultravox_twilio",
                                "error": True,
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

        _ULTRAVOX_DATA_CONNECTION_CONTEXT.pop(token, None)

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
            created = await _create_ultravox_twilio_call(
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
