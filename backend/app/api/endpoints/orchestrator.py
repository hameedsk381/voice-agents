import random
import json
import base64
import uuid
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from starlette.websockets import WebSocketState
from loguru import logger

from app.core import database
from app.core.config import settings
from app.core.security import decode_token
from app.core.deps import get_current_user_required
from app.models.user import User
from app.models import agent as models
from app.schemas.policy import ConversationPolicy, State, Transition, Guardrail
from app.schemas.orchestrator import ChatRequest, ChatResponse, JoinRequest, JoinResponse

from app.orchestration.session_manager import session_manager
from app.services.monitoring_service import monitoring_service
from app.services.hitl_service import HITLService
from app.services.tools.registry import get_tool_schemas
from app.services.agent_registry_service import AgentRegistryService
from app.orchestration.inter_agent_bus import inter_agent_bus

from app.orchestration.turn_processor import TurnProcessor, send_with_tts, stt_service
from app.orchestration.tool_executor import execute_tool


def get_sample_policy():
    return ConversationPolicy(
        initial_state="GREETING",
        states={
            "GREETING": State(
                name="GREETING",
                enforce_script="Hello! I'm your AI assistant. How can I help you today?",
                allowed_intents=["greeting", "ask_help", "billing", "technical", "sales", "account"],
                transitions=[
                    Transition(event="user_spoke", target_state="PROCESSING")
                ]
            ),
            "PROCESSING": State(
                name="PROCESSING",
                allowed_intents=["billing", "technical", "sales", "order", "account", "fallback"],
                transitions=[
                    Transition(event="billing_intent", target_state="BILLING_SUPPORT"),
                    Transition(event="technical_intent", target_state="TECH_SUPPORT"),
                    Transition(event="tool_needed", target_state="WAITING_FOR_TOOL")
                ],
                guardrails=[
                    Guardrail(name="Disallow-Profanity", type="regex", config={"pattern": r"fuck|shit|damn"}, action="block")
                ]
            ),
            "WAITING_FOR_TOOL": State(
                name="WAITING_FOR_TOOL",
                transitions=[
                    Transition(event="tool_complete", target_state="PROCESSING")
                ]
            ),
            "BILLING_SUPPORT": State(
                name="BILLING_SUPPORT",
                enforce_script="I can certainly help you with your billing inquiry. Could you please provide your account number?",
                allowed_intents=["provide_account", "ask_why"],
                guardrails=[
                    Guardrail(name="PII-Check", type="pii", action="mask")
                ]
            ),
            "TECH_SUPPORT": State(
                name="TECH_SUPPORT",
                enforce_script="Technical support here. What seems to be the issue with your service?",
                allowed_intents=["describe_problem"]
            )
        }
    )

router = APIRouter()


def _resolve_agent_config(agent, db, agent_id: str):
    from app.orchestration.agent_config import resolve_active_agent_config
    from app.schemas.policy import ConversationPolicy
    active_persona, active_tools, active_policy_raw = resolve_active_agent_config(db, agent)
    active_policy = None
    if active_policy_raw:
        active_policy = ConversationPolicy.parse_obj(active_policy_raw)
    return active_persona, active_tools or [], active_policy


def _resolve_agent_by_id_or_capability(
    db: Session, agent_id: Optional[str], capability: Optional[str]
) -> models.Agent:
    if capability:
        svc = AgentRegistryService(db)
        agent = svc.find_agent_for_capability(capability)
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"No active agent found for capability '{capability}'",
            )
        return agent
    if not agent_id:
        raise HTTPException(status_code=400, detail="Either agent_id or capability is required")
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/join/{agent_id}", response_model=JoinResponse)
async def join_call(
    agent_id: str,
    body: JoinRequest = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Return session info for a given agent. The client then connects via WebSocket /ws/{agent_id}."""
    body = body or JoinRequest()
    agent = _resolve_agent_by_id_or_capability(db, agent_id, body.capability if body else None)

    session_language = body.language or agent.language or "en-IN"

    return JoinResponse(
        session_id="",
        agent_id=agent_id,
        agent_name=agent.name,
        language=session_language,
        status="ok",
    )


@router.post("/join-by-capability/{capability}", response_model=JoinResponse)
async def join_by_capability(
    capability: str,
    body: JoinRequest = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Discover the best agent for a capability and return session info."""
    body = body or JoinRequest()
    agent = _resolve_agent_by_id_or_capability(db, None, capability)

    session_language = body.language or agent.language or "en-IN"

    return JoinResponse(
        session_id="",
        agent_id=agent.id,
        agent_name=agent.name,
        language=session_language,
        status="ok",
    )


@router.websocket("/ws/{agent_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    agent_id: str,
    db: Session = Depends(database.get_db),
    language: str = Query(None),
    voice: str = Query(None),
    caller_id: str = Query(None),
    token: str = Query(None)
):
    ws_token = token
    if not ws_token:
        ws_token = websocket.query_params.get("token")
    if not ws_token:
        ws_token = websocket.cookies.get("access_token")

    token_data = None
    if ws_token:
        token_data = decode_token(ws_token)

    user = None
    if token_data:
        user = db.query(User).filter(User.id == token_data.user_id).first()

    if not user or not user.is_active:
        if settings.ENVIRONMENT == "dev":
            logger.warning("WS auth skipped (dev mode) — using first user")
            user = db.query(User).first()
        if not user or not user.is_active:
            await websocket.accept()
            await websocket.close(code=4001, reason="Unauthorized")
            return

    await websocket.accept()

    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        await websocket.close(code=4004, reason="Agent not found")
        return

    org_id = agent.organization_id
    active_persona, active_tools, active_policy = _resolve_agent_config(agent, db, agent_id)

    logger.info(f"Session isolation active for organization: {org_id}")

    session_language = language or agent.language or "en-IN"
    session_voice = voice or "auto"

    agent_config = agent.config or {}
    session_id = str(uuid.uuid4())
    await session_manager.create_session(
        session_id=session_id,
        agent_id=agent_id,
        caller_id=caller_id,
        metadata={
            "channel": "websocket",
            "floor_owner": "user",
            "routing_mode": agent_config.get("routing_mode", "standard"),
            "feature_flags": agent_config.get("feature_flags", {}),
        },
    )

    await monitoring_service.broadcast_event(session_id, "session_start", {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "caller_id": caller_id
    })

    session_policy = active_policy or get_sample_policy()
    processor = TurnProcessor(
        db=db,
        websocket=websocket,
        agent=agent,
        agent_id=agent_id,
        session_id=session_id,
        caller_id=caller_id,
        org_id=org_id,
        session_language=session_language,
        session_voice=session_voice,
        active_persona=active_persona,
        active_tools=active_tools,
        tool_schemas=get_tool_schemas(active_tools) if active_tools else None,
        session_policy=session_policy
    )

    await processor.initialize_context()

    asyncio.create_task(processor.voice_ux.precompute_tokens(voice=session_voice))

    await websocket.send_json({
        "type": "session_start",
        "session_id": session_id,
        "agent_name": agent.name
    })

    input_queue = asyncio.Queue()
    current_response_task: asyncio.Task = None

    async def read_websocket():
        try:
            while True:
                data = await websocket.receive_text()
                await input_queue.put(json.loads(data))
        except WebSocketDisconnect:
            await input_queue.put({"type": "disconnect"})
        except Exception as e:
            logger.error(f"WebSocket Read Error: {e}")
            await input_queue.put({"type": "disconnect"})

    reader_task = asyncio.create_task(read_websocket())

    human_input_queue = asyncio.Queue()

    async def listen_for_human_intervention():
        pubsub = await session_manager.get_human_message_listener(session_id)
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    payload = json.loads(message["data"])
                    if payload["type"] == "human_response":
                        await human_input_queue.put(payload["text"])
                        if current_response_task and not current_response_task.done():
                            current_response_task.cancel()
        except asyncio.CancelledError:
            await pubsub.unsubscribe()
        except Exception as e:
            logger.error(f"HITL Listener Error: {e}")

    hitl_task = asyncio.create_task(listen_for_human_intervention())

    # --- Audio accumulation with silence detection ---
    audio_buffer = bytearray()
    audio_flush_task: asyncio.Task = None
    SILENCE_MS = 0.8  # flush after 800ms of no audio chunks

    async def _audio_flush_timer():
        """Wait for silence, then push a flush_audio message."""
        await asyncio.sleep(SILENCE_MS)
        await input_queue.put({"type": "flush_audio"})

    async def _flush_audio_and_process(buf: bytes):
        """Transcribe accumulated audio and process the turn."""
        if not buf:
            return
        import time as _time
        try:
            stt_start = _time.perf_counter()
            transcript = await stt_service.transcribe(
                buf,
                language=session_language,
                mimetype="audio/webm",
            )
            stt_ms = (_time.perf_counter() - stt_start) * 1000
            stt_confidence = transcript.confidence
            logger.info(f"STT [{transcript.provider}] confidence={stt_confidence:.2f} ms={stt_ms:.0f} text={transcript.text!r}")
            if transcript.text:
                await _process_user_input(transcript.text, stt_confidence, stt_ms)
        except Exception as e:
            logger.error(f"STT Error after flush: {e}")

    async def _process_user_input(user_input: str, stt_confidence: float, stt_ms: float):
        """Shared processing logic for user input (speech or text)."""
        nonlocal current_response_task
        hitl_service = HITLService(db)
        intervention = await hitl_service.get_intervention_status(session_id)

        if intervention and intervention.mode == "takeover":
            logger.info(f"Session {session_id} in TAKEOVER mode. Routing user input to HITL.")
            await monitoring_service.broadcast_event(session_id, "hitl_takeover", {"active": True, "agent": intervention.user_id})
            await monitoring_service.broadcast_event(session_id, "transcription", {"text": user_input, "role": "user"})
            try:
                human_text = await asyncio.wait_for(human_input_queue.get(), timeout=60.0)
                await send_with_tts(websocket, human_text, language=session_language, voice=session_voice, sentiment_score=processor.context.sentiment_slope)
                await session_manager.add_to_history(session_id, "user", user_input)
                await session_manager.add_to_history(session_id, "assistant", human_text)
                processor.context.history.append({"role": "user", "content": user_input})
                processor.context.history.append({"role": "assistant", "content": human_text})
                await websocket.send_json({"type": "end_response"})
            except asyncio.TimeoutError:
                logger.warning("HITL Takeover timeout waiting for supervisor response")
            return

        if intervention and intervention.mode == "whisper":
            logger.info(f"Session {session_id} in WHISPER mode. Suggesting response.")
            await monitoring_service.broadcast_event(session_id, "transcription", {"text": user_input, "role": "user"})
            suggestion_prompt = f"{active_persona}\n\nSUGGESTION MODE: Provide a concise response for the supervisor to use."
            suggestion = await processor.llm_service.generate_response(user_input, suggestion_prompt, processor.context.history)
            await monitoring_service.broadcast_event(session_id, "whisper_suggestion", {"suggestion": suggestion, "original_input": user_input})
            try:
                approved_text = await asyncio.wait_for(human_input_queue.get(), timeout=30.0)
            except asyncio.TimeoutError:
                logger.warning("Whisper timeout, falling back to suggestion")
                approved_text = suggestion
            await send_with_tts(websocket, approved_text, language=session_language, voice=session_voice, sentiment_score=processor.context.sentiment_slope)
            await session_manager.add_to_history(session_id, "user", user_input)
            await session_manager.add_to_history(session_id, "assistant", approved_text)
            processor.context.history.append({"role": "user", "content": user_input})
            processor.context.history.append({"role": "assistant", "content": approved_text})
            await websocket.send_json({"type": "end_response"})
            return

        if current_response_task and not current_response_task.done():
            current_response_task.cancel()
        await session_manager.set_floor_owner(session_id, "user")
        current_response_task = asyncio.create_task(
            processor.process_turn(user_input, stt_confidence=stt_confidence, stt_ms=stt_ms)
        )

    try:
        GLOBAL_SILENCE_TIMEOUT = 30.0

        while True:
            try:
                message = await asyncio.wait_for(input_queue.get(), timeout=GLOBAL_SILENCE_TIMEOUT)
            except asyncio.TimeoutError:
                logger.info(f"Global silence in session {session_id}")
                nudge_text = "Are you still there? I'm here to help if you have any more questions."
                await send_with_tts(websocket, nudge_text, language=session_language, voice=session_voice)
                continue

            if message["type"] == "disconnect":
                break

            if message.get("type") == "interrupt":
                if audio_flush_task and not audio_flush_task.done():
                    audio_flush_task.cancel()
                    audio_flush_task = None
                audio_buffer = bytearray()
                await session_manager.set_floor_owner(session_id, "user")
                if current_response_task and not current_response_task.done():
                    current_response_task.cancel()
                    logger.info("Interrupting current response task")
                continue

            # --- Audio accumulation with silent-flush ---
            if message.get("type") == "flush_audio":
                if audio_buffer:
                    buf = bytes(audio_buffer)
                    audio_buffer = bytearray()
                    await _flush_audio_and_process(buf)
                continue

            if "audio" in message:
                try:
                    chunk = base64.b64decode(message["audio"])
                    audio_buffer.extend(chunk)
                    # Reset the silence timer
                    if audio_flush_task and not audio_flush_task.done():
                        audio_flush_task.cancel()
                    audio_flush_task = asyncio.create_task(_audio_flush_timer())
                except Exception as e:
                    logger.error(f"Audio decode error: {e}")
                continue

            # --- Non-audio message (text, etc.) ---
            # Flush any pending audio first
            if audio_buffer:
                if audio_flush_task and not audio_flush_task.done():
                    audio_flush_task.cancel()
                    audio_flush_task = None
                buf = bytes(audio_buffer)
                audio_buffer = bytearray()
                await _flush_audio_and_process(buf)

            if "text" in message:
                user_input = message["text"]
                stt_confidence = float(message.get("stt_confidence", 1.0))
                stt_ms = 0.0
                if user_input:
                    await _process_user_input(user_input, stt_confidence, stt_ms)

    except Exception as e:
        logger.error(f"Orchestrator Loop Error: {e}")
    finally:
        reader_task.cancel()
        hitl_task.cancel()
        if audio_flush_task and not audio_flush_task.done():
            audio_flush_task.cancel()
        if current_response_task and not current_response_task.done():
            current_response_task.cancel()

        await processor.log_session_completion()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(database.get_db)):
    """Experimental: Stateless/REST Chat connector for Text Agents."""
    agent = db.query(models.Agent).filter(models.Agent.id == request.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    session_id = request.session_id or str(uuid.uuid4())
    org_id = agent.organization_id

    from app.services.memory import get_memory_service
    from app.orchestration.agent_orchestrator import AgentOrchestrator
    from app.services.llm.enterprise_llm import EnterpriseLLM

    memory_service = get_memory_service(db)
    orchestrator = AgentOrchestrator(db, policy=get_sample_policy())
    llm_service = EnterpriseLLM()

    await session_manager.connect()
    session = await session_manager.get_session(session_id)
    if not session:
        await session_manager.create_session(session_id, request.agent_id, request.caller_id, metadata={"channel": "rest"})
        history = []
    else:
        history = await session_manager.get_history(session_id)

    intent, _intent_conf = orchestrator.detect_intent(request.text)

    response_text = await llm_service.generate_response(
        request.text,
        agent.persona,
        history
    )

    await session_manager.add_to_history(session_id, "user", request.text)
    await session_manager.add_to_history(session_id, "assistant", response_text)

    return ChatResponse(
        session_id=session_id,
        text=response_text,
        agent_id=request.agent_id,
        metadata={"org_id": org_id}
    )


@router.get("/voices")
async def get_voices(primaryLanguage: Optional[str] = None):
    """List available voices from the active TTS provider."""
    from app.orchestration.turn_processor import tts_service
    return await tts_service.get_voices()
