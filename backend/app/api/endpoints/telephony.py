"""
Telephony endpoints — multi-provider inbound/outbound.
Supports Twilio, Vonage, Plivo, Telnyx media streaming.
"""
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketState
from loguru import logger

from app.orchestration.tool_executor import execute_tool
from app.core import database
from app.core.config import settings
from app.models import agent as models
from app.orchestration.session_manager import session_manager
from app.services.monitoring_service import monitoring_service
from app.services.telephony_service import telephony_service
from app.services.telephony.factory import get_telephony_provider
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
    """Inbound voice webhook — routes to configured agent (Twilio, Vonage, Plivo)."""
    provider = get_telephony_provider()

    agent = db.query(models.Agent).filter(models.Agent.is_active == True).first()
    if not agent:
        logger.warning("No active agent found for inbound call")
        return _hangup_response(provider, "No active agent is configured. Goodbye.")

    stream_url = f"{_ws_base_url()}/api/v1/telephony/stream/{agent.id}"
    provider_name = (settings.TELEPHONY_PROVIDER or "twilio").lower()

    try:
        if provider_name == "twilio":
            form = await request.form()
            caller_number = form.get("From", "unknown")
            called_number = form.get("To", "unknown")
            call_sid = form.get("CallSid", "unknown")
            logger.info(f"Twilio inbound call from {caller_number} to {called_number} (SID: {call_sid})")

            twilio_client = telephony_service.get_twilio_client()
            if not twilio_client:
                return _hangup_response(provider, "Service is not available. Goodbye.")

            twiml = provider.generate_stream_twiml(
                stream_url,
                welcome_message="Connecting you to our AI assistant. Please wait.",
            )
            return Response(content=twiml, media_type="application/xml")

        elif provider_name == "vonage":
            body = await request.json()
            logger.info(f"Vonage inbound call: {body.get('uuid')}")
            ncco = provider.generate_stream_twiml(stream_url)
            return JSONResponse(content=json.loads(ncco))

        elif provider_name == "plivo":
            form = await request.form()
            logger.info(f"Plivo inbound call from {form.get('From', 'unknown')}")
            plivo_xml = provider.generate_stream_twiml(
                stream_url,
                welcome_message="Connecting you to our AI assistant. Please wait.",
            )
            return Response(content=plivo_xml, media_type="application/xml")

        else:
            return _hangup_response(provider, "Provider not supported for inbound calls yet.")

    except Exception as exc:
        logger.error(f"Inbound call setup failed: {exc}")
        return _hangup_response(provider, "An error occurred. Please try again later.")


def _hangup_response(provider, message: str) -> Response:
    provider_name = (settings.TELEPHONY_PROVIDER or "twilio").lower()
    if provider_name == "vonage":
        ncco = [{"action": "talk", "text": message}, {"action": "hangup"}]
        return JSONResponse(content=ncco)
    elif provider_name == "plivo":
        xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Speak>{message}</Speak><Hangup/></Response>'
        return Response(content=xml, media_type="application/xml")
    else:
        from twilio.twiml.voice_response import VoiceResponse
        resp = VoiceResponse()
        resp.say(message, voice="Polly.Joanna")
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
    """Trigger an outbound call via the configured telephony provider."""
    if request.headers.get("content-type", "").startswith("application/json"):
        body = await request.json()
    else:
        form = await request.form()
        body = dict(form)

    agent_id = body.get("agent_id")
    to_number = body.get("to") or body.get("called_number")
    from_number = body.get("from") or settings.TWILIO_PHONE_NUMBER or ""

    if not agent_id or not to_number:
        return Response(status_code=400, content="Missing agent_id or to number")

    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        return Response(status_code=404, content="Agent not found")

    provider = get_telephony_provider()
    webhook_url = f"{_https_base_url()}/api/v1/telephony/twiml?agent_id={agent_id}"

    call_id = await provider.initiate_outbound_call(
        to_number=to_number,
        from_number=from_number,
        webhook_url=webhook_url,
    )

    if call_id:
        logger.info(f"Outbound call initiated via {settings.TELEPHONY_PROVIDER}: ID={call_id}")
        return {"status": "initiated", "call_id": call_id, "to": to_number, "provider": settings.TELEPHONY_PROVIDER}
    else:
        return Response(status_code=500, content="Call initiation failed — check provider credentials")


@router.get("/twiml")
async def twiml_redirect(
    agent_id: str = Query(...),
    format: str = Query(None),
    request: Request = None,
):
    """Return provider-specific streaming instructions (TwiML / NCCO / XML)."""
    stream_url = f"{_ws_base_url()}/api/v1/telephony/stream/{agent_id}"
    provider = get_telephony_provider()

    result = provider.generate_stream_twiml(stream_url)
    provider_name = (settings.TELEPHONY_PROVIDER or "twilio").lower()

    if provider_name == "vonage" or format == "ncco":
        return JSONResponse(content=json.loads(result))
    return Response(content=result, media_type="application/xml")
