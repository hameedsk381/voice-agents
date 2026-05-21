import json
import base64
import uuid
import asyncio
import websockets
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import WebSocket
from starlette.websockets import WebSocketState
from loguru import logger

from app.core.config import settings
from app.models import agent as models
from app.services.ultravox_service import UltravoxService
from app.orchestration.session_manager import session_manager
from app.services.monitoring_service import monitoring_service
from app.orchestration.ultravox_call import (
    build_ultravox_selected_tools,
    build_system_prompt,
    extract_agent_tool_names,
)
from app.orchestration.audio_handler import pcm16le_to_wav_bytes
from app.orchestration.tool_executor import execute_tool
from app.services.compliance_service import compliance_validator, redactor, get_baseline_rules
from app.models.compliance import AuditLog

ultravox_service = UltravoxService()

def is_ultravox_runtime() -> bool:
    """True when Ultravox should handle voice (STT/LLM/TTS)."""
    if settings.VOICE_RUNTIME == "custom":
        return settings.USE_ULTRAVOX_RUNTIME and ultravox_service.enabled
    return ultravox_service.enabled


def _use_ultravox_runtime() -> bool:
    return is_ultravox_runtime()

async def _run_ultravox_compliance_audit(
    session_id: str,
    agent_id: str,
    organization_id: Optional[str],
    turn_index: int,
    user_input: str,
    ai_response: str,
    state_name: str = "ULTRAVOX_RUNTIME",
) -> None:
    """Thread-safe and loop-safe compliance auditor for Ultravox proxy sessions."""
    if not user_input or not ai_response:
        return

    from app.core.database import SessionLocal
    from fastapi.concurrency import run_in_threadpool

    def fetch_rules():
        with SessionLocal() as local_db:
            return get_baseline_rules(db=local_db, organization_id=organization_id)

    rules = await run_in_threadpool(fetch_rules)
    audit_result = await compliance_validator.validate_turn(
        user_input,
        ai_response,
        rules,
        turn_index,
    )

    def save_audit():
        with SessionLocal() as local_db:
            audit_log = AuditLog(
                session_id=session_id,
                turn_index=turn_index,
                user_message=redactor.redact_text(user_input),
                ai_response=redactor.redact_text(ai_response),
                is_compliant=audit_result.is_compliant,
                violations=[v.dict() for v in audit_result.violations],
                risk_score=audit_result.risk_score,
                agent_id=agent_id,
                organization_id=organization_id,
                state_name=state_name,
            )
            local_db.add(audit_log)
            local_db.commit()

    await run_in_threadpool(save_audit)

    if not audit_result.is_compliant:
        await monitoring_service.broadcast_event(
            session_id,
            "compliance_alert",
            {
                "severity": "critical",
                "risk_score": audit_result.risk_score,
                "violations": [v.rule_name for v in audit_result.violations],
            },
        )

async def run_ultravox_proxy_session(
    websocket: WebSocket,
    agent: models.Agent,
    agent_id: str,
    db: Session,
    active_persona: Optional[str] = None,
    active_tools: Optional[List[Any]] = None,
    language: Optional[str] = None,
    voice: Optional[str] = None,
    caller_id: Optional[str] = None,
):
    """
    Medium-scope runtime:
    Keep this backend as control-plane but proxy realtime voice runtime to Ultravox.
    """
    session_language = language or agent.language or "en-US"
    selected_voice = voice if voice and voice != "auto" else settings.ULTRAVOX_VOICE
    org_id = agent.organization_id
    tool_list = active_tools if active_tools is not None else agent.tools
    selected_tools = build_ultravox_selected_tools(tool_list, implementation="client")
    system_prompt = build_system_prompt(agent, active_persona, session_language)

    call = await ultravox_service.create_server_websocket_call(
        system_prompt=system_prompt,
        voice=selected_voice,
        metadata={
            "agent_id": agent_id,
            "org_id": org_id,
            "channel": "websocket",
        },
        selected_tools=selected_tools,
        initial_state={"agent_id": agent_id, "organization_id": org_id},
    )

    join_url = call.get("joinUrl")
    call_id = call.get("callId")
    if not join_url:
        raise RuntimeError("Ultravox did not return joinUrl")

    session_id = call_id or str(uuid.uuid4())
    await session_manager.create_session(
        session_id=session_id,
        agent_id=agent_id,
        caller_id=caller_id,
        metadata={"channel": "ultravox_proxy", "org_id": org_id}
    )

    await monitoring_service.broadcast_event(session_id, "session_start", {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "caller_id": caller_id,
        "provider": "ultravox",
    })

    await websocket.send_json({
        "type": "session_start",
        "session_id": session_id,
        "agent_name": agent.name,
        "provider": "ultravox",
    })

    transcript_buffers: Dict[tuple, str] = {}
    unanswered_user_turns: List[str] = []
    turn_count = 0
    closed_by_client = False

    async with websockets.connect(join_url, max_size=None) as uvx_ws:
        async def client_to_ultravox():
            nonlocal closed_by_client
            while True:
                try:
                    client_message = await websocket.receive_text()
                except WebSocketDisconnect:
                    closed_by_client = True
                    break

                try:
                    payload = json.loads(client_message)
                except json.JSONDecodeError:
                    continue

                if "text" in payload and payload["text"]:
                    user_text = str(payload["text"])
                    await uvx_ws.send(json.dumps({
                        "type": "user_text_message",
                        "text": user_text,
                        "urgency": "immediate"
                    }))
                    continue

                if "audio" in payload:
                    try:
                        raw_audio = base64.b64decode(payload["audio"])
                    except Exception:
                        logger.warning("Failed to decode client audio payload")
                        continue
                    await uvx_ws.send(raw_audio)

        async def ultravox_to_client():
            nonlocal turn_count
            async for uvx_message in uvx_ws:
                if isinstance(uvx_message, (bytes, bytearray)):
                    wav_audio = pcm16le_to_wav_bytes(
                        bytes(uvx_message),
                        sample_rate=settings.ULTRAVOX_OUTPUT_SAMPLE_RATE,
                    )
                    await websocket.send_json({
                        "type": "audio",
                        "data": base64.b64encode(wav_audio).decode("utf-8"),
                    })
                    continue

                try:
                    event = json.loads(uvx_message)
                except json.JSONDecodeError:
                    logger.warning("Received non-JSON text message from Ultravox")
                    continue

                event_type = event.get("type")

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

                    if role == "agent":
                        chunk = delta or (full_text if not is_final else "")
                        if chunk:
                            await websocket.send_json({"type": "text_chunk", "text": chunk})

                    if is_final:
                        final_text = transcript_buffers.pop(key, full_text or delta).strip()
                        if final_text:
                            mapped_role = "assistant" if role == "agent" else "user"
                            await session_manager.add_to_history(session_id, mapped_role, final_text)
                            await monitoring_service.broadcast_event(session_id, "transcription", {
                                "text": final_text,
                                "role": mapped_role
                            })
                            if mapped_role == "user":
                                unanswered_user_turns.append(final_text)
                            else:
                                user_turn_for_audit = (
                                    unanswered_user_turns.pop(0)
                                    if unanswered_user_turns
                                    else ""
                                )
                                if user_turn_for_audit:
                                    turn_count += 1
                                    try:
                                        await _run_ultravox_compliance_audit(
                                            session_id=session_id,
                                            agent_id=agent_id,
                                            organization_id=org_id,
                                            turn_index=turn_count,
                                            user_input=user_turn_for_audit,
                                            ai_response=final_text,
                                        )
                                    except Exception as audit_error:
                                        logger.error(f"Ultravox compliance audit failed: {audit_error}")

                        if role == "agent":
                            await websocket.send_json({"type": "end_response"})
                    continue

                if event_type == "state":
                    await monitoring_service.broadcast_event(session_id, "ultravox_state", {
                        "state": event.get("state")
                    })
                    continue

                if event_type in {
                    "client_tool_invocation",
                    "data_connection_tool_invocation",
                    "tool_invocation",  # Legacy fallback
                }:
                    tool_name = event.get("toolName") or event.get("name")
                    invocation_id = event.get("invocationId") or event.get("id")
                    tool_arguments = (
                        event.get("parameters")
                        or event.get("toolCallArguments")
                        or {}
                    )
                    if not isinstance(tool_arguments, dict):
                        tool_arguments = {}

                    await websocket.send_json({
                        "type": "tool_call",
                        "name": tool_name,
                        "arguments": tool_arguments,
                    })
                    await monitoring_service.broadcast_event(session_id, "tool_call", {
                        "name": tool_name,
                        "arguments": tool_arguments,
                        "provider": "ultravox",
                    })

                    result_message_type = (
                        "data_connection_tool_result"
                        if event_type == "data_connection_tool_invocation"
                        else "client_tool_result"
                    )

                    if not invocation_id:
                        logger.warning(f"Ultravox tool invocation missing invocationId: {event}")
                        continue

                    if not tool_name:
                        await uvx_ws.send(json.dumps({
                            "type": result_message_type,
                            "invocationId": invocation_id,
                            "responseType": "tool-response",
                            "errorType": "undefined",
                            "errorMessage": "Tool name missing in invocation.",
                        }))
                        continue

                    try:
                        result = await execute_tool(
                            tool_name,
                            tool_arguments,
                            db,
                            agent_id,
                            session_id,
                        )
                        await uvx_ws.send(json.dumps({
                            "type": result_message_type,
                            "invocationId": invocation_id,
                            "result": result,
                            "responseType": "tool-response",
                        }))
                        await monitoring_service.broadcast_event(session_id, "tool_result", {
                            "name": tool_name,
                            "arguments": tool_arguments,
                            "result": result,
                            "provider": "ultravox",
                        })
                        await websocket.send_json({
                            "type": "tool_result",
                            "name": tool_name,
                            "result": result,
                        })
                    except Exception as tool_error:
                        logger.error(f"Ultravox tool execution failed ({tool_name}): {tool_error}")
                        await uvx_ws.send(json.dumps({
                            "type": result_message_type,
                            "invocationId": invocation_id,
                            "responseType": "tool-response",
                            "errorType": "implementation-error",
                            "errorMessage": str(tool_error),
                        }))
                        await websocket.send_json({
                            "type": "tool_error",
                            "name": tool_name,
                            "message": str(tool_error),
                        })
                        await monitoring_service.broadcast_event(session_id, "tool_result", {
                            "name": tool_name,
                            "arguments": tool_arguments,
                            "result": str(tool_error),
                            "provider": "ultravox",
                            "error": True,
                        })
                    continue

                if event_type == "playback_clear_buffer":
                    await websocket.send_json({"type": "playback_clear_buffer"})
                    continue

                if event_type == "debug":
                    logger.debug(f"Ultravox debug event: {event}")
                    continue

        client_task = asyncio.create_task(client_to_ultravox())
        ultravox_task = asyncio.create_task(ultravox_to_client())

        done, pending = await asyncio.wait(
            [client_task, ultravox_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()

        for task in done:
            if task.cancelled():
                continue
            exc = task.exception()
            from starlette.websockets import WebSocketDisconnect
            if exc and not isinstance(exc, WebSocketDisconnect):
                raise exc

    await session_manager.end_session(
        session_id,
        "client_disconnect" if closed_by_client else "ultravox_closed"
    )
    if websocket.client_state != WebSocketState.DISCONNECTED:
        await websocket.close()
