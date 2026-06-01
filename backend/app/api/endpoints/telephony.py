"""
Telephony endpoints for Twilio inbound/outbound voice.
Ultravox Twilio medium removed — Samvaad Twilio integration TBD.
"""
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketState
from twilio.twiml.voice_response import VoiceResponse
from loguru import logger

from app.orchestration.tool_executor import execute_tool
from app.core import database
from app.core.config import settings
from app.models import agent as models
from app.orchestration.session_manager import session_manager
from app.services.monitoring_service import monitoring_service
from app.services.telephony_service import telephony_service
from app.services.tools.registry import AVAILABLE_TOOLS

import json
import os
import random
import uuid

router = APIRouter()


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
    if "localhost" in host or host.startswith("127.0.0.1"):
        return f"http://{host.rstrip('/')}"
    return f"https://{host.rstrip('/')}"


def _build_selected_tools(tools: Optional[List[Any]]) -> List[Dict[str, Any]]:
    selected = []
    if not tools:
        return selected
    for t in tools:
        if isinstance(t, str):
            if t in AVAILABLE_TOOLS:
                schema = AVAILABLE_TOOLS[t].get("input_schema", {})
                selected.append({
                    "temporaryTool": {
                        "modelToolName": t,
                        "description": AVAILABLE_TOOLS[t].get("description", ""),
                        "dynamicParameters": _tool_json_schema_to_dynamic_parameters(schema),
                    }
                })
            else:
                logger.warning(f"Skipping unknown tool '{t}' for telephony")
        elif isinstance(t, dict):
            selected.append(t)
    return selected


def _tool_json_schema_to_dynamic_parameters(schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    params = []
    properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
    required = schema.get("required", []) if isinstance(schema, dict) else []
    for prop_name, prop_schema in properties.items():
        if isinstance(prop_schema, dict):
            params.append({
                "name": prop_name,
                "location": "PARAMETER_LOCATION_BODY",
                "schema": prop_schema,
                "required": prop_name in required,
            })
    return params


@router.post("/incoming")
async def incoming_call(request: Request, db: Session = Depends(database.get_db)):
    """Twilio inbound voice webhook — routes to configured agent."""
    form = await request.form()
    caller_number = form.get("From", "unknown")
    called_number = form.get("To", "unknown")
    call_sid = form.get("CallSid", "unknown")

    logger.info(f"Inbound call from {caller_number} to {called_number} (SID: {call_sid})")

    agent = db.query(models.Agent).filter(models.Agent.is_active == True).first()
    if not agent:
        logger.warning("No active agent found for inbound call")
        resp = VoiceResponse()
        resp.say("No active agent is configured. Goodbye.", voice="Polly.Joanna")
        resp.hangup()
        return Response(content=str(resp), media_type="application/xml")

    twilio_client = telephony_service.get_twilio_client()
    if not twilio_client:
        logger.error("Twilio client not configured")
        resp = VoiceResponse()
        resp.say("Service is not available. Goodbye.", voice="Polly.Joanna")
        resp.hangup()
        return Response(content=str(resp), media_type="application/xml")

    try:
        stream_url = f"{_ws_base_url()}/api/v1/telephony/stream/{agent.id}"
        resp = VoiceResponse()
        start = resp.connect()
        start.stream(url=stream_url)
        resp.say("Connecting you to our AI assistant. Please wait.", voice="Polly.Joanna")

        logger.info(f"Inbound call {call_sid} → stream to agent {agent.id}")
        return Response(content=str(resp), media_type="application/xml")
    except Exception as exc:
        logger.error(f"Inbound call setup failed: {exc}")
        resp = VoiceResponse()
        resp.say("An error occurred. Please try again later.", voice="Polly.Joanna")
        resp.hangup()
        return Response(content=str(resp), media_type="application/xml")


@router.websocket("/stream/{agent_id}")
async def legacy_media_stream(
    websocket: WebSocket,
    agent_id: str,
    db: Session = Depends(database.get_db),
):
    """Twilio Media Streams endpoint — legacy fallback path."""
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        await websocket.accept()
        await websocket.close(code=4004, reason="Agent not found")
        return

    from app.orchestration.turn_processor import TurnProcessor, send_with_tts, stt_service
    from app.services.tools.registry import get_tool_schemas
    session_language = agent.language or "en-IN"
    session_voice = "auto"
    session_id = str(uuid.uuid4())

    org_id = agent.organization_id
    session_policy = None

    await websocket.accept()
    await session_manager.create_session(
        session_id=session_id,
        agent_id=agent_id,
        metadata={"channel": "twilio_stream", "floor_owner": "user"},
    )

    processor = TurnProcessor(
        db=db,
        websocket=websocket,
        agent=agent,
        agent_id=agent_id,
        session_id=session_id,
        org_id=org_id,
        session_language=session_language,
        session_voice=session_voice,
    )
    await processor.initialize_context()

    input_queue = asyncio.Queue()
    current_response_task = None

    async def read_stream():
        try:
            while True:
                raw = await websocket.receive_text()
                msg = json.loads(raw)
                if msg.get("event") == "media":
                    payload = msg["media"].get("payload", "")
                    await input_queue.put({"type": "audio", "audio": payload, "mimetype": "audio/wav"})
                elif msg.get("event") == "stop":
                    await input_queue.put({"type": "disconnect"})
                    break
        except WebSocketDisconnect:
            await input_queue.put({"type": "disconnect"})
        except Exception as e:
            logger.error(f"Stream read error: {e}")
            await input_queue.put({"type": "disconnect"})

    reader_task = asyncio.create_task(read_stream())

    try:
        while True:
            message = await input_queue.get()
            if message["type"] == "disconnect":
                break

            audio_data = base64.b64decode(message["audio"])
            transcript = await stt_service.transcribe(audio_data, language=session_language, mimetype=message.get("mimetype", "audio/wav"))
            user_input = transcript.text

            if user_input:
                if current_response_task and not current_response_task.done():
                    current_response_task.cancel()
                current_response_task = asyncio.create_task(
                    processor.process_turn(user_input, stt_confidence=transcript.confidence)
                )
    except Exception as e:
        logger.error(f"Stream loop error: {e}")
    finally:
        reader_task.cancel()
        if current_response_task and not current_response_task.done():
            current_response_task.cancel()
        await processor.log_session_completion()


@router.get("/outgoing")
async def outgoing_call_form():
    """Simple form to trigger an outbound call (manual test)."""
    return Response(
        content="""<html><body>
        <h2>Outbound Call</h2>
        <form action="/api/v1/telephony/outgoing" method="post">
            <label>Agent ID: <input name="agent_id" size="40"/></label><br/>
            <label>To: <input name="to" placeholder="+15551234567"/></label><br/>
            <label>From: <input name="from" placeholder="+15550001111"/></label><br/>
            <button type="submit">Call</button>
        </form></body></html>""",
        media_type="text/html",
    )


@router.post("/outgoing")
async def outgoing_call(
    request: Request,
    db: Session = Depends(database.get_db),
):
    """Trigger an outbound call — legacy fallback path."""
    if request.headers.get("content-type", "").startswith("application/json"):
        body = await request.json()
    else:
        form = await request.form()
        body = dict(form)

    agent_id = body.get("agent_id")
    to_number = body.get("to") or body.get("called_number")
    from_number = body.get("from") or os.getenv("TWILIO_PHONE_NUMBER")

    if not agent_id or not to_number:
        return Response(status_code=400, content="Missing agent_id or to number")

    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        return Response(status_code=404, content="Agent not found")

    twilio_client = telephony_service.get_twilio_client()
    if not twilio_client:
        return Response(status_code=500, content="Twilio not configured")

    try:
        stream_url = f"{_https_base_url()}/api/v1/telephony/stream/{agent_id}"
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect><Stream url="{stream_url}"/></Connect>
</Response>"""

        call = twilio_client.calls.create(
            url=f"{_https_base_url()}/api/v1/telephony/twiml?agent_id={agent_id}",
            to=to_number,
            from_=from_number,
        )
        logger.info(f"Outbound call initiated: SID={call.sid}")
        return {"status": "initiated", "call_sid": call.sid, "to": to_number}
    except Exception as exc:
        logger.error(f"Outbound call failed: {exc}")
        return Response(status_code=500, content=str(exc))


@router.get("/twiml")
async def twiml_redirect(agent_id: str = Query(...), request: Request = None):
    """Return TwiML that points to the media stream."""
    stream_url = f"{_ws_base_url()}/api/v1/telephony/stream/{agent_id}"
    resp = VoiceResponse()
    start = resp.connect()
    start.stream(url=stream_url)
    return Response(content=str(resp), media_type="application/xml")
