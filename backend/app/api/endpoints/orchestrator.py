from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.core import database
from app.core.config import settings
from app.services.llm.openai_provider import OpenAILLM
from app.services.llm.openai_provider import OpenAILLM
from app.services.llm.groq_provider import GroqLLM
# from app.services.stt.deepgram_provider import DeepgramSTT
from app.services.tts.deepgram_provider import DeepgramTTS
from app.services.tts.qwen_provider import QwenTTS
from app.services.stt.mock_provider import MockSTT
from app.services.tts.mock_provider import MockTTS
from app.services.tools.registry import get_tool_schemas, AVAILABLE_TOOLS
from app.services.memory import get_memory_service
from app.models import agent as models
from app.orchestration.session_manager import session_manager
from app.orchestration.agent_orchestrator import AgentOrchestrator, AgentContext, ConversationFlow, ConversationState
from app.orchestration.langgraph_orchestrator import LangGraphOrchestrator
from app.services.monitoring_service import monitoring_service
from app.services.analytics_service import AnalyticsService
from app.services.hitl_service import HITLService
from loguru import logger
import json
import os
import base64
import uuid
import time
import asyncio
from datetime import datetime

router = APIRouter()

# Initialize providers
if settings.GROQ_API_KEY:
    logger.info("Using Real Groq LLM")
    llm_service = GroqLLM()
else:
    logger.warning("No GROQ_API_KEY found. Using OpenAI/Mock fallback")
    llm_service = OpenAILLM(api_key=settings.OPENAI_API_KEY)

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

async def execute_tool(tool_name: str, arguments: dict, db: Session, agent_id: str, session_id: str = None) -> str:
    """Execute a tool and return the result."""
    if tool_name not in AVAILABLE_TOOLS:
        return f"Tool '{tool_name}' not found."
        
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


async def send_with_tts(websocket: WebSocket, text: str, language: str = "en-US", voice: str = None):
    """Send text response with TTS audio."""
    await websocket.send_json({"type": "text_chunk", "text": text})
    
    audio_bytes = await tts_service.synthesize(text, language=language, voice=voice)
    if audio_bytes:
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        await websocket.send_json({"type": "audio", "data": audio_b64})


async def stream_response_with_tts(websocket: WebSocket, llm_stream, session_id: str = None, language: str = "en-US", voice: str = None):
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
                audio_bytes = await tts_service.synthesize(current_sentence, language=language, voice=voice)
                if audio_bytes:
                    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                    await websocket.send_json({"type": "audio", "data": audio_b64})
                current_sentence = ""
    
    # Flush remaining
    if len(current_sentence.strip()) > 2:
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


@router.websocket("/ws/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str, language: str = None, voice: str = None, db: Session = Depends(database.get_db)):
    await websocket.accept()
    
    # Fetch agent configuration
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        await websocket.close(code=4004, reason="Agent not found")
        return

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
    orchestrator = AgentOrchestrator(db)
    flow = ConversationFlow(session_id=session_id)
    memory_service = get_memory_service(db)
    analytics_service = AnalyticsService(db)
    
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
        extracted_info={}
    )

    logger.info(f"Session {session_id} started for agent: {agent.name}")
    
    # Load Tools
    agent_tool_names = agent.tools if agent.tools else []
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
    
    async def process_turn(user_input: str):
        nonlocal turn_count, agent  # Access outer scope variables
        try:
            # Broadcast transcription
            await monitoring_service.broadcast_event(session_id, "transcription", {
                "text": user_input,
                "role": "user"
            })
            
            # Update state
            flow.next_state("user_spoke")
            turn_count += 1
            turn_start_time = time.time()
            
            # Detect intent
            context.current_intent = orchestrator.detect_intent(user_input)
            if context.current_intent:
                await websocket.send_json({"type": "intent_detected", "intent": context.current_intent})
            
            # Agent Selection (Dynamic Routing)
            selected_agent = await orchestrator.select_agent(context, agent_id)
            if selected_agent.id != agent.id:
                await websocket.send_json({
                    "type": "agent_switch",
                    "from": agent.name,
                    "to": selected_agent.name,
                    "reason": f"Routing for {context.current_intent}"
                })
                agent = selected_agent
            
            # Prompt Construction
            system_prompt = f"{agent.persona}\n\nIMPORTANT: Respond only in {session_language}."
            await websocket.send_json({"type": "start_response"})
            
            # Orchestration Strategy
            use_langgraph = "multi-agent" in (agent.description or "").lower()
            
            full_response = ""
            
            if use_langgraph:
                logger.info("Using LangGraph")
                lg_orchestrator = LangGraphOrchestrator(agent_id=agent_id, session_id=session_id, language=session_language)
                history = [{"role": h["role"], "content": h["content"]} for h in context.history]
                full_response = await lg_orchestrator.get_response(user_input, history)
                
                # Fake stream for consistency
                async def fake_stream(text):
                    for word in text.split(" "):
                        yield word + " "
                        await asyncio.sleep(0.02)
                
                await stream_response_with_tts(websocket, fake_stream(full_response), session_id, language=session_language, voice=session_voice)
                
                context.history.append({"role": "user", "content": user_input})
                context.history.append({"role": "assistant", "content": full_response})

            elif tool_schemas and hasattr(llm_service, 'generate_with_tools'):
                text_response, tool_calls = await llm_service.generate_with_tools(
                    user_input, system_prompt, context.history, tools=tool_schemas
                )
                
                if tool_calls:
                    flow.next_state("tool_needed")
                    tool_results = []
                    for tc in tool_calls:
                        await websocket.send_json({"type": "tool_call", "arguments": tc["arguments"]})
                        result = await execute_tool(tc["name"], tc["arguments"], db, agent_id, session_id)
                        tool_results.append({"tool": tc["name"], "result": result})
                    
                    flow.next_state("tool_complete")
                    tool_context = "\n".join([f"[Tool: {tr['tool']}] Result: {tr['result']}" for tr in tool_results])
                    
                    context.history.append({"role": "user", "content": user_input})
                    context.history.append({"role": "assistant", "content": f"Tool results:\n{tool_context}"})
                    
                    full_response = await stream_response_with_tts(
                        websocket,
                        llm_service.generate_stream(
                            f"Based on: {tool_context}", system_prompt, context.history
                        ),
                        session_id, language=session_language, voice=session_voice
                    )
                    context.history.append({"role": "assistant", "content": full_response})
                else:
                    if text_response:
                        await send_with_tts(websocket, text_response, language=session_language, voice=session_voice)
                        context.history.append({"role": "user", "content": user_input})
                        context.history.append({"role": "assistant", "content": text_response})
                        full_response = text_response
            else:
                full_response = await stream_response_with_tts(
                    websocket,
                    llm_service.generate_stream(user_input, system_prompt, context.history),
                    session_id, language=session_language, voice=session_voice
                )
                context.history.append({"role": "user", "content": user_input})
                context.history.append({"role": "assistant", "content": full_response})

            # Escalation Check
            should_escalate, reason = orchestrator.should_escalate(context, full_response)
            if should_escalate:
                flow.next_state("escalate")
                await websocket.send_json({"type": "escalation", "reason": reason})
                await session_manager.escalate_session(session_id, reason)
                await send_with_tts(websocket, "Transferring you to a human agent.", language=session_language, voice=session_voice)
                return "ESCALATED"
            
            # Save History & Metrics
            await session_manager.add_to_history(session_id, "user", user_input)
            await session_manager.add_to_history(session_id, "assistant", full_response)
            
            latency = (time.time() - turn_start_time) * 1000
            latencies.append(latency)
            
            await websocket.send_json({"type": "end_response"})

        except asyncio.CancelledError:
            logger.info("Response generation cancelled (Barge-In)")
            raise
        except Exception as e:
            logger.error(f"Error in turn: {e}")
            await websocket.send_json({"type": "error", "message": str(e)})

    try:
        while True:
            # Wait for next input
            message = await input_queue.get()
            
            if message.get("type") == "disconnect":
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
                "status": "completed",
                "transcript": context.history
            })
            await session_manager.end_session(session_id, "client_disconnect")
        except Exception as e:
            logger.error(f"Cleanup Error: {e}")
@router.get("/voices")
async def get_voices():
    """Proxy to get available voices from QwenTTS."""
    return await tts_service.get_voices()
