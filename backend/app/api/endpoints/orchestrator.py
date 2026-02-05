from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.core import database
from app.core.config import settings

from app.services.llm.groq_provider import GroqLLM
from app.services.llm.enterprise_llm import EnterpriseLLM
# from app.services.stt.deepgram_provider import DeepgramSTT
from app.services.tts.deepgram_provider import DeepgramTTS
from app.services.tts.qwen_provider import QwenTTS
from app.services.stt.mock_provider import MockSTT
from app.services.tts.mock_provider import MockTTS
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
from datetime import datetime
import inspect
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
    """Proxy to get available voices from QwenTTS."""
    return await tts_service.get_voices()
