from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketState
from app.core import database
from app.core.config import settings

from app.services.llm.groq_provider import GroqLLM
from app.services.llm.enterprise_llm import EnterpriseLLM
# from app.services.stt.deepgram_provider import DeepgramSTT
from app.services.tts.deepgram_provider import DeepgramTTS
from app.services.tts.qwen_provider import QwenTTS
from app.services.stt.mock_provider import MockSTT
from app.services.tts.mock_provider import MockTTS
from app.services.ultravox_service import UltravoxService
from app.services.tools.registry import get_tool_schemas, AVAILABLE_TOOLS
from app.services.memory import get_memory_service
from app.orchestration.agent_swarm import SwarmOrchestrator
import random
from app.models import agent as models
from app.orchestration.session_manager import session_manager
from app.orchestration.agent_orchestrator import (
    AgentOrchestrator, AgentContext, ConversationFlow, 
    ConversationState, ConfidenceScores, MemoryItem, MemoryType
)
from app.orchestration.langgraph_orchestrator import LangGraphOrchestrator
from app.services.monitoring_service import monitoring_service
from app.services.analytics_service import AnalyticsService
from app.services.hitl_service import HITLService
from app.services.compliance_service import compliance_validator, redactor, get_baseline_rules
from app.services.voice_ux_service import VoiceUXService
from app.services.shadow_service import ShadowComparisonService
from app.services.knowledge_service import KnowledgeService
from app.services.tools.mcp_service import mcp_client
from app.orchestration.tool_planner import get_tool_planner
from app.models.compliance import AuditLog
from loguru import logger
import json
import os
import base64
import uuid
import time
import asyncio
import io
import wave
from datetime import datetime
import inspect
import websockets
from app.schemas.policy import ConversationPolicy, State, Transition, Guardrail
from app.schemas.orchestrator import ChatRequest, ChatResponse

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
ultravox_service = UltravoxService()

# Initialize providers
if settings.GROQ_API_KEY:
    logger.info("Using Real Groq LLM")
    llm_service = GroqLLM()
else:
    logger.error("No GROQ_API_KEY found. Groq LLM required.")
    # You might want a different fallback or raise an error
    llm_service = GroqLLM() 

# Use Deepgram if key exists, otherwise Mock
if settings.DEEPGRAM_API_KEY:
    logger.info("Using Real Deepgram Services")
    # stt_service = DeepgramSTT() # Switched to Frontend Web Speech API
    stt_service = MockSTT()
    # tts_service = DeepgramTTS() # Replaced by QwenTTS
    tts_service = QwenTTS()
    logger.info("Using QwenTTS Service & Frontend STT")
else:
    logger.warning("Using MOCK Services (No DEEPGRAM_API_KEY)")
    stt_service = MockSTT()
    # tts_service = MockTTS() # Replaced by QwenTTS for testing if local server is up
    tts_service = QwenTTS()
    logger.info("Using QwenTTS Service (with Mock STT)")


def _use_ultravox_runtime() -> bool:
    return settings.USE_ULTRAVOX_RUNTIME and ultravox_service.enabled


def _pcm16le_to_wav_bytes(
    pcm_bytes: bytes,
    sample_rate: int,
    channels: int = 1,
    sample_width: int = 2,
) -> bytes:
    """Wraps raw PCM audio into WAV for browser-friendly playback."""
    with io.BytesIO() as wav_buffer:
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_bytes)
        return wav_buffer.getvalue()


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
        safe_schema: Dict[str, Any]
        if isinstance(param_schema, dict):
            safe_schema = param_schema
        else:
            safe_schema = {"type": "string", "description": f"Parameter {param_name}"}

        dynamic_parameters.append(
            {
                "name": param_name,
                "location": "PARAMETER_LOCATION_BODY",
                "schema": safe_schema,
                "required": param_name in required_names,
            }
        )

    return dynamic_parameters


def _build_ultravox_selected_tools(tools: Optional[List[Any]]) -> List[Dict[str, Any]]:
    selected_tools: List[Dict[str, Any]] = []
    for tool_name in _extract_agent_tool_names(tools):
        tool = AVAILABLE_TOOLS.get(tool_name)
        if not tool:
            logger.warning(f"Skipping unknown tool '{tool_name}' in Ultravox selectedTools mapping")
            continue

        selected_tools.append(
            {
                "temporaryTool": {
                    "modelToolName": tool.name,
                    "description": tool.description,
                    "dynamicParameters": _tool_json_schema_to_ultravox_dynamic_parameters(
                        tool.parameters or {}
                    ),
                    "client": {},
                }
            }
        )

    return selected_tools


async def _run_ultravox_compliance_audit(
    db: Session,
    session_id: str,
    agent_id: str,
    organization_id: Optional[str],
    turn_index: int,
    user_input: str,
    ai_response: str,
    state_name: str = "ULTRAVOX_RUNTIME",
) -> None:
    if not user_input or not ai_response:
        return

    rules = get_baseline_rules(db=db, organization_id=organization_id)
    audit_result = await compliance_validator.validate_turn(
        user_input,
        ai_response,
        rules,
        turn_index,
    )

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
    db.add(audit_log)
    db.commit()

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


async def execute_tool(tool_name: str, arguments: dict, db: Session, agent_id: str, session_id: str = None) -> str:
    """Execute a tool and return the result."""
    if tool_name not in AVAILABLE_TOOLS:
        # Fallback to MCP (Model Context Protocol) Tools
        mcp_tools = await mcp_client.list_tools()
        if any(t["name"] == tool_name for t in mcp_tools):
            logger.info(f"Executing Tool '{tool_name}' via MCP Server")
            return await mcp_client.call_tool(tool_name, arguments)
            
        return f"Tool '{tool_name}' not found in local registry or MCP."
        
    tool = AVAILABLE_TOOLS[tool_name]
    
    # Check if tool requires human approval
    if tool.requires_approval:
        hitl_service = HITLService(db)
        action = await hitl_service.create_pending_action(
            session_id=session_id,
            agent_id=agent_id,
            action_type=tool.name,
            description=f"Action requested by AI: {tool.name} with args {arguments}",
            payload=arguments
        )
        return f"The tool '{tool_name}' requires human authorization. I've submitted a request for approval (ID: {action.id[:8]}). I will continue once authorized."

    # Normal execution
    result = await tool.execute(**arguments)
    logger.info(f"Tool '{tool_name}' executed with result: {result}")
    
    # Log tool call in session
    if session_id:
        await session_manager.log_tool_call(session_id, tool_name, arguments, result)
    
    return result


async def send_with_tts(websocket: WebSocket, text: str, language: str = "en-US", voice: str = None, sentiment_score: float = None):
    """Send text response with TTS audio (sentiment-aware)."""
    await websocket.send_json({"type": "text_chunk", "text": text})
    
    # Infer instruction from sentiment
    instruct = None
    if sentiment_score is not None:
        if sentiment_score < 0.3:
            instruct = "empathetic, soft, apologetic"
        elif sentiment_score > 0.8:
            instruct = "excited, happy, energetic"
        else:
            instruct = "professional, calm"

    # Check support
    sig = inspect.signature(tts_service.synthesize)
    if 'instruct' in sig.parameters:
        audio_bytes = await tts_service.synthesize(text, language=language, voice=voice, instruct=instruct)
    else:
        audio_bytes = await tts_service.synthesize(text, language=language, voice=voice)

    if audio_bytes:
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        await websocket.send_json({"type": "audio", "data": audio_b64})


async def stream_response_with_tts(websocket: WebSocket, llm_stream, session_id: str = None, language: str = "en-US", voice: str = None, sentiment_score: float = None):
    """Stream LLM response with sentence-buffered TTS."""
    full_response = ""
    current_sentence = ""
    
    async for chunk in llm_stream:
        full_response += chunk
        current_sentence += chunk
        await websocket.send_json({"type": "text_chunk", "text": chunk})
        
        # Broadcast chunk to monitoring
        if session_id:
            await monitoring_service.broadcast_event(session_id, "text_chunk", {"text": chunk})
        
        # TTS on sentence boundaries
        if any(punct in chunk for punct in [".", "?", "!", "\n"]):
            if len(current_sentence.strip()) > 5:
                # Infer instruction
                instruct = None
                if sentiment_score is not None:
                    if sentiment_score < 0.3: instruct = "empathetic, soft"
                    elif sentiment_score > 0.8: instruct = "excited"
                    else: instruct = "professional"

                if 'instruct' in inspect.signature(tts_service.synthesize).parameters:
                    audio_bytes = await tts_service.synthesize(current_sentence, language=language, voice=voice, instruct=instruct)
                else:
                    audio_bytes = await tts_service.synthesize(current_sentence, language=language, voice=voice)
                    
                if audio_bytes:
                    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                    await websocket.send_json({"type": "audio", "data": audio_b64})
                current_sentence = ""
    
    # Flush remaining
    if len(current_sentence.strip()) > 2:
        if 'instruct' in inspect.signature(tts_service.synthesize).parameters:
            audio_bytes = await tts_service.synthesize(current_sentence, language=language, voice=voice, instruct=instruct if 'instruct' in locals() else None)
        else:
            audio_bytes = await tts_service.synthesize(current_sentence, language=language, voice=voice)

        if audio_bytes:
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            await websocket.send_json({"type": "audio", "data": audio_b64})
    
    # Broadcast full response completion
    if session_id:
        await monitoring_service.broadcast_event(session_id, "transcription", {
            "text": full_response,
            "role": "assistant"
        })
    
    return full_response


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
    persona_prompt = active_persona or agent.persona
    selected_tools = _build_ultravox_selected_tools(active_tools if active_tools is not None else agent.tools)

    system_prompt = (
        f"{persona_prompt}\n\n"
        f"IMPORTANT: Respond only in {session_language}."
    )

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
                    wav_audio = _pcm16le_to_wav_bytes(
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
                                            db=db,
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
            if exc and not isinstance(exc, WebSocketDisconnect):
                raise exc

    await session_manager.end_session(
        session_id,
        "client_disconnect" if closed_by_client else "ultravox_closed"
    )
    if websocket.client_state != WebSocketState.DISCONNECTED:
        await websocket.close()


@router.websocket("/ws/{agent_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    agent_id: str, 
    db: Session = Depends(database.get_db),
    language: str = Query(None),
    voice: str = Query(None),
    caller_id: str = Query(None)
):
    await websocket.accept()
    
    # Fetch agent configuration
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        await websocket.close(code=4004, reason="Agent not found")
        return

    # Multi-tenancy Isolation (Moved up to use for version queries if needed, though agent is already fetched)
    org_id = agent.organization_id
    
    active_persona = agent.persona
    active_tools = agent.tools or []
    active_policy = None
    
    # Canary / A/B Routing Logic
    versions = db.query(models.AgentVersion).filter(models.AgentVersion.agent_id == agent_id, models.AgentVersion.weight > 0).all()
    if versions:
        # Weighted selection
        total_weight = sum(v.weight for v in versions)
        if total_weight > 0:
            rand_val = random.randint(1, 100)
            cumulative = 0
            for v in versions:
                cumulative += v.weight
                if rand_val <= cumulative:
                    logger.info(f"A/B Route: Using Version {v.version_number} (Weight: {v.weight}%)")
                    active_persona = v.persona
                    active_tools = v.tools
                    if v.policy:
                        from app.schemas.policy import ConversationPolicy
                        active_policy = ConversationPolicy.parse_obj(v.policy)
                    break

    # Manual Pinning overrides A/B
    elif agent.active_version_id:
        version = db.query(models.AgentVersion).filter(models.AgentVersion.id == agent.active_version_id).first()
        if version:
            logger.info(f"Using pinned Version {version.version_number} for agent {agent.name}")
            active_persona = version.persona
            active_tools = version.tools
            if version.policy:
                from app.schemas.policy import ConversationPolicy
                active_policy = ConversationPolicy.parse_obj(version.policy)

    # Medium scope runtime switch:
    # Keep control-plane in this backend but route realtime speech path through Ultravox.
    if _use_ultravox_runtime():
        try:
            await run_ultravox_proxy_session(
                websocket=websocket,
                agent=agent,
                agent_id=agent_id,
                db=db,
                active_persona=active_persona,
                active_tools=active_tools,
                language=language,
                voice=voice,
                caller_id=caller_id,
            )
        except Exception as e:
            logger.error(f"Ultravox proxy session failed: {e}")
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.send_json({"type": "error", "message": f"Ultravox runtime error: {str(e)}"})
                await websocket.close(code=1011, reason="Ultravox runtime error")
        return

    logger.info(f"Session isolation active for organization: {org_id}")

    # Use requested language or fallback to agent default
    session_language = language or agent.language or "en-US"
    session_voice = voice or "auto"

    # Create session
    session_id = str(uuid.uuid4())
    await session_manager.create_session(
        session_id=session_id,
        agent_id=agent_id,
        caller_id=None,
        metadata={"channel": "websocket"}
    )
    
    # Broadcast session start
    await monitoring_service.broadcast_event(session_id, "session_start", {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "caller_id": None
    })
    
    # Initialize services
    session_policy = active_policy or get_sample_policy()
    orchestrator = AgentOrchestrator(db, policy=session_policy)
    llm_service = EnterpriseLLM(primary_model="llama-3.3-70b-versatile") # Use Enhanced Enterprise LLM
    # flow = ConversationFlow(session_id=session_id) # Replaced by PolicyEngine via Orchestrator
    memory_service = get_memory_service(db)
    user_context = ""
    if caller_id:
        user_context = await memory_service.get_context_for_call(caller_id, organization_id=org_id)
        logger.info(f"Loaded memory context for user {caller_id} (Org: {org_id})")
    
    analytics_service = AnalyticsService(db)
    voice_ux = VoiceUXService(tts_service)
    shadow_service = ShadowComparisonService(db)

    # Pre-cache UX tokens (Non-blocking)
    asyncio.create_task(voice_ux.precompute_tokens(voice=session_voice))
    
    # Tracking
    session_start_dt = datetime.utcnow()
    latencies = []
    turn_count = 0
    token_count = 0
    
    # Context
    context = AgentContext(
        session_id=session_id,
        caller_id=None,
        history=[],
        current_intent=None,
        extracted_info={},
        current_state=session_policy.initial_state,
        confidence=ConfidenceScores(),
        memory=[user_context] if user_context else [],
        sentiment_slope=0.8, # Start positive
        metadata={"org_id": org_id}
    )

    logger.info(f"Session {session_id} started for agent: {agent.name}")
    
    # Load Tools
    agent_tool_names = active_tools if active_tools else []
    tool_schemas = get_tool_schemas(agent_tool_names) if agent_tool_names else None
    
    await websocket.send_json({
        "type": "session_start",
        "session_id": session_id,
        "agent_name": agent.name
    })
    
    # Queues and Tasks
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

    # Start reader
    reader_task = asyncio.create_task(read_websocket())
    
    # HITL Listener Task
    human_input_queue = asyncio.Queue()
    
    async def listen_for_human_intervention():
        pubsub = await session_manager.get_human_message_listener(session_id)
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    payload = json.loads(message["data"])
                    if payload["type"] == "human_response":
                        await human_input_queue.put(payload["text"])
                        # If a response is pending, cancel it to allow human response
                        if current_response_task and not current_response_task.done():
                            current_response_task.cancel()
        except asyncio.CancelledError:
            await pubsub.unsubscribe()
        except Exception as e:
            logger.error(f"HITL Listener Error: {e}")

    hitl_task = asyncio.create_task(listen_for_human_intervention())
    
    def is_fast_path_turn(text: str) -> Optional[str]:
        """Check for turns that don't need expensive LLM reasoning."""
        text_lower = text.lower().strip().strip(".?!")
        acknowledgements = {
            "ok": "Got it.",
            "okay": "I understand.",
            "thanks": "You're welcome.",
            "thank you": "My pleasure.",
            "hello": "Hi there! How can I help?",
            "hi": "Hello! How can I help you?",
            "bye": "Goodbye! Have a great day.",
            "yes": "Okay.",
            "no": "Alright."
        }
        return acknowledgements.get(text_lower)

    async def process_turn(user_input: str):
        nonlocal turn_count, agent, token_count
        try:
            # 1. Track Metrics & Sentiment
            turn_count += 1
            turn_start_time = time.time()
            
            # Update Sentiment Slope (Moving Average)
            current_sentiment = orchestrator.analyze_sentiment(user_input)
            context.sentiment_slope = (context.sentiment_slope * 0.7) + (current_sentiment * 0.3)

            # 2. Fast Path Check (Elite Feature)
            fast_response = is_fast_path_turn(user_input)
            if fast_response:
                logger.info("Fast Path Triggered")
                await send_with_tts(websocket, fast_response, language=session_language, voice=session_voice, sentiment_score=context.sentiment_slope)
                await session_manager.add_to_history(session_id, "user", user_input)
                await session_manager.add_to_history(session_id, "assistant", fast_response)
                await websocket.send_json({"type": "end_response"})
                return

            # 3. Check for HITL Intervention
            hitl_service = HITLService(db)
            intervention = await hitl_service.get_intervention_status(session_id)
            
            # CASE A: HUMAN TAKEOVER
            if intervention and intervention.mode == "takeover":
                logger.info(f"Session {session_id} in TAKEOVER mode.")
                await monitoring_service.broadcast_event(session_id, "hitl_takeover", {"active": True, "agent": intervention.user_id})
                
                try:
                    human_text = await asyncio.wait_for(human_input_queue.get(), timeout=60.0)
                    await send_with_tts(websocket, human_text, language=session_language, voice=session_voice, sentiment_score=context.sentiment_slope)
                    await session_manager.add_to_history(session_id, "user", user_input)
                    await session_manager.add_to_history(session_id, "assistant", human_text)
                    await websocket.send_json({"type": "end_response"})
                    return
                except asyncio.TimeoutError:
                    return

            # Broadcast user transcription to monitoring
            await monitoring_service.broadcast_event(session_id, "transcription", {
                "text": user_input,
                "role": "user"
            })
            
            # Voice UX: Micro-acknowledgement for longer inputs (Elite Feature)
            if len(user_input.split()) > 10:
                # Send a quick "mm-hm" or "Right" to signal the user was heard
                await voice_ux.send_backchannel(websocket)
            
            # 3. Policy Engine: Input Guard & State Transition
            context.current_intent = orchestrator.detect_intent(user_input)
            
            # Confidence Check (Elite Feature)
            # In production, these scores come from STT (Deepgram/OpenAI) and LLM logprobs
            context.confidence.stt = 0.95 # Mocked for demo
            context.confidence.intent = 0.9 if context.current_intent else 0.7
            context.confidence.overall = (context.confidence.stt + context.confidence.intent) / 2
            
            # Handle Low Confidence Early
            confidence_response = orchestrator.handle_low_confidence(context)
            if confidence_response:
                logger.warning(f"Low Confidence handoff triggered: {context.confidence.overall}")
                await send_with_tts(websocket, confidence_response, language=session_language, voice=session_voice, sentiment_score=context.sentiment_slope)
                await websocket.send_json({"type": "end_response"})
                return

            if orchestrator.policy_engine:
                is_allowed, reason = orchestrator.policy_engine.validate_input(
                    context.current_state, user_input, context.current_intent
                )
                if not is_allowed:
                    await send_with_tts(websocket, f"I'm sorry, I cannot process that request. {reason}", language=session_language, voice=session_voice, sentiment_score=context.sentiment_slope)
                    await websocket.send_json({"type": "end_response"})
                    return
                
                context.current_state = orchestrator.policy_engine.get_next_state(context.current_state, "user_spoke")
                if context.current_intent:
                    context.current_state = orchestrator.policy_engine.get_next_state(context.current_state, f"{context.current_intent}_intent")

            # 4. Agent Selection (Dynamic Swarm Routing)
            swarm = SwarmOrchestrator(db, agent)
            available_specialists = orchestrator.get_agents_by_role("specialist")
            
            # Elite feature: if supervisor, route to specialist
            if agent.role == "supervisor" or "swarm" in (agent.description or "").lower():
                selected_agent = await swarm.route_task(user_input, context.history, available_specialists)
                
                # PEAK AGENTIC FEATURE: Autonomous Discovery
                # If pool selection failed to find a worker, search the whole Org dynamically
                if selected_agent.id == agent.id:
                    discovered_agent = await swarm.discover_and_hire(user_input)
                    if discovered_agent:
                        selected_agent = discovered_agent
                        await websocket.send_json({
                            "type": "agent_discovery",
                            "name": discovered_agent.name,
                            "capability": user_input[:50]
                        })

                if selected_agent.id != agent.id:
                    await websocket.send_json({
                        "type": "agent_switch",
                        "from": agent.name, "to": selected_agent.name,
                        "reason": "Swarm Delegation"
                    })
                    agent = selected_agent
            else:
                # Standard routing
                selected_agent = await orchestrator.select_agent(context, agent_id)
                if selected_agent.id != agent.id:
                    agent = selected_agent
            
            # PEAK AGENTIC FEATURE: Knowledge Retrieval (RAG)
            knowledge_context = ""
            knowledge_service = KnowledgeService(db)
            relevant_chunks = await knowledge_service.query_knowledge(agent.id, user_input, limit=2)
            
            if relevant_chunks:
                logger.info(f"RAG: Found {len(relevant_chunks)} relevant knowledge chunks.")
                knowledge_context = "\n\nUSE THESE FACTS FROM YOUR KNOWLEDGE BASE IF RELEVANT:\n" + \
                                    "\n".join([f"- {c['content']}" for c in relevant_chunks])
                await websocket.send_json({"type": "knowledge_hit", "count": len(relevant_chunks)})

            # 5. Response Generation (AI or Whisper)
            full_response = ""
            response_sent = False
            LATENCY_BUDGET = 2.5 # Max seconds for reasoning path before we degrade UX
            
            # CASE B: WHISPER MODE
            if intervention and intervention.mode == "whisper":
                logger.info(f"Session {session_id} in WHISPER mode. Generating suggestion for supervisor.")
                
                # Generate a quick suggestion (non-streaming for speed)
                suggestion_prompt = f"{active_persona}{knowledge_context}\n\nSUGGESTION MODE: Provide a concise response for the supervisor to use."
                suggestion = await llm_service.generate_response(user_input, suggestion_prompt, context.history)
                
                # Broadcast suggestion to supervisor console
                await monitoring_service.broadcast_event(session_id, "whisper_suggestion", {
                    "suggestion": suggestion,
                    "original_input": user_input
                })
                
                try:
                    logger.info("Waiting for supervisor to approve/edit suggestion...")
                    full_response = await asyncio.wait_for(human_input_queue.get(), timeout=30.0)
                except asyncio.TimeoutError:
                    logger.warning("Whisper timeout, falling back to original suggestion")
                    full_response = suggestion
            
            # NORMAL AI RESPONSE
            if not full_response:
                system_prompt = f"{active_persona}{knowledge_context}\n\nIMPORTANT: Respond only in {session_language}."
                await websocket.send_json({"type": "start_response"})
                
                # elite cost awareness
                if token_count > (agent.token_limit or 50000):
                    logger.warning(f"TOKEN BUDGET EXCEEDED ({token_count}). Switching to fallback model: {agent.fallback_model}")
                    llm_service.model = agent.fallback_model or "llama-3.1-8b-instant"

                try:
                    # Voice UX: Send a "filler" if we expect a long reasoning path
                    is_reasoning_path = "multi-agent" in (agent.description or "").lower() or tool_schemas is not None
                    if is_reasoning_path:
                        # Send a random filler to bridge the latency gap
                        await voice_ux.send_filler(websocket)

                    # Enforce Latency Budget per Step
                    # Check for LangGraph (Complex Reasoning Path)
                    if "multi-agent" in (agent.description or "").lower():
                        lg_orchestrator = LangGraphOrchestrator(agent_id=agent_id, session_id=session_id, language=session_language)
                        full_response = await asyncio.wait_for(
                            lg_orchestrator.get_response(user_input, context.history),
                            timeout=LATENCY_BUDGET
                        )
                    
                    # Strategic Tool Planning (Elite Feature)
                    elif tool_schemas and hasattr(llm_service, 'generate_with_tools'):
                        planner = get_tool_planner()
                        # Hybrid Approach: Use planner to decide and explain, or use LLM tool calling
                        plan_statement, tool_calls = await planner.generate_plan(user_input, context.history, tool_schemas)
                        
                        if plan_statement:
                            # Step 2 of 'agents.md': Explain the plan to the user immediately
                            await send_with_tts(websocket, plan_statement, language=session_language, voice=session_voice, sentiment_score=context.sentiment_slope)
                            logger.info(f"Speaking Plan: {plan_statement}")
                        
                        # If planner didn't find tools, fallback to standard tool generation
                        if not tool_calls:
                            text_response, tool_calls = await asyncio.wait_for(
                                llm_service.generate_with_tools(user_input, system_prompt, context.history, tools=tool_schemas),
                                timeout=LATENCY_BUDGET
                            )
                        
                        if tool_calls:
                            if orchestrator.policy_engine:
                                context.current_state = orchestrator.policy_engine.get_next_state(context.current_state, "tool_needed")
                            
                            tool_results = []
                            for tc in tool_calls:
                                await websocket.send_json({"type": "tool_call", "arguments": tc["arguments"]})
                                result = await execute_tool(tc["name"], tc["arguments"], db, agent_id, session_id)
                                tool_results.append({"tool": tc["name"], "result": result})
                            
                            if orchestrator.policy_engine:
                                context.current_state = orchestrator.policy_engine.get_next_state(context.current_state, "tool_complete")
                            
                            tool_context = "\n".join([f"[Tool: {tr['tool']}] Result: {tr['result']}" for tr in tool_results])
                            full_response = await stream_response_with_tts(
                                websocket,
                                llm_service.generate_stream(f"Based on: {tool_context}", system_prompt, context.history),
                                session_id, language=session_language, voice=session_voice, sentiment_score=context.sentiment_slope
                            )
                            response_sent = True
                        else:
                            full_response = text_response
                    
                    # Default Stream
                    else:
                        full_response = await stream_response_with_tts(
                            websocket,
                            llm_service.generate_stream(user_input, system_prompt, context.history),
                            session_id, language=session_language, voice=session_voice, sentiment_score=context.sentiment_slope
                        )
                        response_sent = True
                        
                except asyncio.TimeoutError:
                    logger.warning(f"LATENCY BUDGET EXCEEDED ({LATENCY_BUDGET}s). Entering Degradation Mode.")
                    full_response = "I'm looking into that for you. One moment please..."
                    await send_with_tts(websocket, full_response, language=session_language, voice=session_voice, sentiment_score=context.sentiment_slope)
                    response_sent = True

            # 6. Policy Engine: Output Guard
            if orchestrator.policy_engine:
                is_valid, validated_text = orchestrator.policy_engine.validate_response(context.current_state, full_response)
                
                # Dynamic Security: Critical states trigger inline compliance audit
                state_config = session_policy.states.get(context.current_state)
                if state_config and state_config.is_sensitive:
                    logger.info(f"Inline Compliance Audit triggered for sensitive state: {context.current_state}")
                    rules = get_baseline_rules(db=db, organization_id=org_id) # In prod, fetch org-specific rules
                    audit_result = await compliance_validator.validate_turn(user_input, validated_text, rules, turn_count)
                    
                    if not audit_result.is_compliant:
                        logger.warning(f"CRITICAL COMPLIANCE VIOLATION in sensitive state: {audit_result.risk_score}")
                        validated_text = "I'm sorry, I cannot fulfill that request due to regulatory constraints."
                        if any(v.severity == "critical" for v in audit_result.violations):
                            await websocket.send_json({"type": "compliance_alert", "risk_score": audit_result.risk_score})
                
                full_response = validated_text

            # 7. Final Delivery (if not streamed)
            if full_response and not response_sent:
                # PEAK AGENTIC FEATURE: Self-Correction Loop
                # (Applied to non-streamed paths and WHISPER mode suggestions)
                full_response = await orchestrator.reflect_and_correct(
                    user_input, full_response, context, agent, llm_service
                )
                await send_with_tts(websocket, full_response, language=session_language, voice=session_voice, sentiment_score=context.sentiment_slope)

            # 8. Escalation & History
            should_escalate, reason = orchestrator.should_escalate(context, full_response, agent)
            if should_escalate:
                await session_manager.escalate_session(session_id, reason)
                await send_with_tts(websocket, "One moment, transferring you to a specialist.", language=session_language, voice=session_voice, sentiment_score=context.sentiment_slope)
                return "ESCALATED"
            
            await session_manager.add_to_history(session_id, "user", user_input)
            await session_manager.add_to_history(session_id, "assistant", full_response)
            context.history.append({"role": "user", "content": user_input})
            context.history.append({"role": "assistant", "content": full_response})
            
            latency = (time.time() - turn_start_time) * 1000
            latencies.append(latency)
            
            # Update Token Count (Estimation: 1.3 tokens per word)
            turn_tokens = int((len(user_input.split()) + len(full_response.split())) * 1.3)
            token_count += turn_tokens
            logger.info(f"Turn Tokens: {turn_tokens}, Total Session Tokens: {token_count}")
            
            # 9. Compliance & Audit (Shadow Audit)
            # Use Background task to not block the voice turn
            async def run_compliance_audit():
                # Get rules for current state or agent
                rules = get_baseline_rules(db=db, organization_id=org_id) # Fetch baseline plus optional agent-specific rules
                audit_result = await compliance_validator.validate_turn(
                    user_input, full_response, rules, turn_count
                )
                
                # Save Audit Log
                audit_log = AuditLog(
                    session_id=session_id,
                    turn_index=turn_count,
                    user_message=redactor.redact_text(user_input),
                    ai_response=redactor.redact_text(full_response),
                    is_compliant=audit_result.is_compliant,
                    violations=[v.dict() for v in audit_result.violations],
                    risk_score=audit_result.risk_score,
                    agent_id=agent_id,
                    organization_id=org_id,
                    state_name=context.current_state
                )
                db.add(audit_log)
                db.commit()
                
                # If critical violation, notify monitoring/supervisor
                if not audit_result.is_compliant:
                    await monitoring_service.broadcast_event(session_id, "compliance_alert", {
                        "severity": "critical",
                        "violations": [v.rule_name for v in audit_result.violations]
                    })

            asyncio.create_task(run_compliance_audit())

            # 10. Shadow Comparison (Elite Feature)
            # Compare with a cheaper model (Llama-3-8b via Groq)
            asyncio.create_task(shadow_service.compare_turn(
                session_id=session_id,
                turn_index=turn_count,
                user_input=user_input,
                system_prompt=active_persona,
                history=context.history,
                primary_response=full_response,
                primary_model_name="groq-llama-3-3-70b", # Corrected name
                primary_latency=latency,
                organization_id=org_id,
                tools=tool_schemas if 'is_reasoning_path' in locals() and is_reasoning_path else None
            ))
            
            await websocket.send_json({"type": "end_response"})
            logger.info(f"Turn {turn_count} complete. Latency: {latency:.2f}ms. Compliance: {len(latencies)}")

        except asyncio.CancelledError:
            logger.info("Response generation cancelled (Barge-In)")
            raise
        except Exception as e:
            logger.error(f"Error in turn: {e}")
            await websocket.send_json({"type": "error", "message": str(e)})

    try:
        # 0. Silence Detection Loop
        SILENCE_THRESHOLD = 30.0 # Seconds before we nudge or end
        
        while True:
            try:
                # Wait for user input with a timeout for silence detection
                message = await asyncio.wait_for(input_queue.get(), timeout=SILENCE_THRESHOLD)
            except asyncio.TimeoutError:
                # Handle Silence
                logger.info(f"Silence detected in session {session_id}")
                nudge_text = "Are you still there? I'm here to help if you have any more questions."
                await send_with_tts(websocket, nudge_text, language=session_language, voice=session_voice)
                # If it happens again, we might want to end the call, for now just nudge once per 30s
                continue

            if message["type"] == "disconnect":
                break
            
            if message.get("type") == "interrupt":
                if current_response_task and not current_response_task.done():
                    current_response_task.cancel()
                    logger.info("Interrupting current response task")
                continue
                
            user_input = ""
            if "audio" in message:
                try:
                    audio_data = base64.b64decode(message["audio"])
                    # Use webm if capturing from browser
                    user_input = await stt_service.transcribe(
                        audio_data, 
                        language=session_language,
                        mimetype="audio/webm"
                    )
                except Exception as e:
                    logger.error(f"STT Error: {e}")
                    continue
            elif "text" in message:
                user_input = message["text"]
            
            if user_input:
                # Barge-in: Cancel any active response
                if current_response_task and not current_response_task.done():
                    current_response_task.cancel()
                
                # Start new response
                current_response_task = asyncio.create_task(process_turn(user_input))

    except Exception as e:
        logger.error(f"Orchestrator Loop Error: {e}")
    finally:
        reader_task.cancel()
        hitl_task.cancel()
        if current_response_task and not current_response_task.done():
            current_response_task.cancel()
            
        # Cleanup & Logging (same as before)
        try:
            avg_lat = sum(latencies)/len(latencies) if latencies else 0
            duration = (datetime.utcnow() - session_start_dt).total_seconds()
            await analytics_service.log_call_completion({
                "session_id": session_id,
                "agent_id": agent_id,
                "caller_id": None,
                "start_time": session_start_dt,
                "duration": duration,
                "avg_latency": avg_lat,
                "turns": turn_count,
                "tokens": token_count,
                "org_id": org_id,
                "status": "completed",
                "transcript": context.history
            }, agent=agent)
            
            # Post-Call Memory Governance
            if caller_id:
                # 1. Summarize
                await memory_service.summarize_conversation(
                    session_id=session_id,
                    user_id=caller_id,
                    agent_id=agent_id,
                    conversation=context.history,
                    outcome=agent.success_criteria[0] if agent.success_criteria else "unknown",
                    llm_service=llm_service,
                    organization_id=org_id
                )
                # 2. Extract specific fact memories
                await memory_service.memorize_from_conversation(
                    user_id=caller_id,
                    conversation=context.history,
                    agent_id=agent_id,
                    session_id=session_id,
                    llm_service=llm_service,
                    organization_id=org_id
                )

            await session_manager.end_session(session_id, "client_disconnect")
        except Exception as e:
            logger.error(f"Cleanup Error: {e}")
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(database.get_db)):
    """Experimental: Stateless/REST Chat connector for Text Agents."""
    agent = db.query(models.Agent).filter(models.Agent.id == request.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    session_id = request.session_id or str(uuid.uuid4())
    org_id = agent.organization_id
    
    # Initialize basic services
    memory_service = get_memory_service(db)
    orchestrator = AgentOrchestrator(db, policy=get_sample_policy()) # Simple for now
    llm_service = EnterpriseLLM()
    
    # 1. Update Session / History
    # Note: In a real enterprise app, we'd retrieve session state from Redis/DB
    await session_manager.connect()
    session = await session_manager.get_session(session_id)
    if not session:
        await session_manager.create_session(session_id, request.agent_id, request.caller_id, metadata={"channel": "rest"})
        history = []
    else:
        history = await session_manager.get_history(session_id)

    # 2. Context
    context = AgentContext(
        session_id=session_id,
        caller_id=request.caller_id,
        history=history,
        current_intent=None,
        extracted_info={},
        metadata={"org_id": org_id}
    )

    # 3. Simple Turn Logic (Synchronous for REST)
    # Detect Intent
    intent = orchestrator.detect_intent(request.text)
    context.current_intent = intent
    
    # Generate Response (Non-streaming for REST POST)
    response_text = await llm_service.generate_response(
        request.text, 
        agent.persona, 
        history
    )
    
    # 4. Save & Return
    await session_manager.add_to_history(session_id, "user", request.text)
    await session_manager.add_to_history(session_id, "assistant", response_text)
    
    # Analytics (Non-blocking)
    analytics_service = AnalyticsService(db)
    # Background log would go here...
    
    return ChatResponse(
        session_id=session_id,
        text=response_text,
        agent_id=request.agent_id,
        metadata={"org_id": org_id}
    )


@router.get("/voices")
async def get_voices():
    """Proxy to get available voices from active voice runtime provider."""
    if _use_ultravox_runtime():
        return await ultravox_service.list_voices()
    return await tts_service.get_voices()
