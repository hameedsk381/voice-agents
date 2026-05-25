import inspect
import base64
import time
import uuid
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import WebSocket
from loguru import logger

from app.core.config import settings
from app.models import agent as models
from app.services.llm.groq_provider import GroqLLM
from app.services.llm.enterprise_llm import EnterpriseLLM
from app.services.tts.qwen_provider import QwenTTS
from app.services.stt.factory import get_stt_provider
from app.services.memory import get_memory_service
from app.core.telemetry import get_tracer, persist_span, async_trace_span
from app.orchestration.turn_metrics import TurnMetrics
from app.orchestration.agent_swarm import SwarmOrchestrator
from app.orchestration.session_manager import session_manager
from app.orchestration.agent_orchestrator import (
    AgentOrchestrator, AgentContext, ConfidenceScores
)
from app.services.monitoring_service import monitoring_service
from app.services.analytics_service import AnalyticsService
from app.services.hitl_service import HITLService
from app.services.compliance_service import compliance_validator, redactor, get_baseline_rules
from app.services.voice_ux_service import VoiceUXService
from app.services.shadow_service import ShadowComparisonService
from app.services.knowledge_service import KnowledgeService
from app.services.checkpoint_service import CheckpointService
from app.services.audit_service import AuditService
from app.orchestration.tool_planner import get_tool_planner
from app.core.metrics import turn_latency_ms, errors_total
from app.orchestration.tool_executor import execute_tool
from app.orchestration.inter_agent_bus import inter_agent_bus
from app.services.emotion_service import EmotionTracker
from app.services.end_of_call_service import EndOfCallService

# Instantiate default providers once
stt_service = get_stt_provider()
tts_service = QwenTTS()

# Model cost rates ($ per 1M input tokens)
MODEL_COST_RATES: Dict[str, float] = {
    "llama-3.3-70b-versatile": 0.59,
    "llama-3.1-8b-instant": 0.18,
    "llama-3.2-3b-preview": 0.06,
    "mixtral-8x7b-32768": 0.24,
    "gemma2-9b-it": 0.20,
    "gpt-4o": 2.50,
    "gpt-4o-mini": 0.15,
    "claude-3-5-sonnet": 3.00,
    "claude-3-haiku": 0.25,
}

async def send_with_tts(
    websocket: WebSocket,
    text: str,
    language: str = "en-US",
    voice: str = None,
    sentiment_score: float = None,
    sent_tracker: list = None,
    metrics: TurnMetrics = None,
    tone_hint: str = None,
):
    """Send text response with TTS audio (sentiment + emotion aware)."""
    if sent_tracker is not None:
        sent_tracker.append(text)
    await websocket.send_json({"type": "text_chunk", "text": text})
    
    # Infer instruction from sentiment or tone hint
    instruct = tone_hint
    if not instruct and sentiment_score is not None:
        if sentiment_score < 0.3:
            instruct = "empathetic, soft, apologetic"
        elif sentiment_score > 0.8:
            instruct = "excited, happy, energetic"
        else:
            instruct = "professional, calm"

    tts_start = time.perf_counter()
    sig = inspect.signature(tts_service.synthesize)
    if 'instruct' in sig.parameters:
        audio_bytes = await tts_service.synthesize(text, language=language, voice=voice, instruct=instruct)
    else:
        audio_bytes = await tts_service.synthesize(text, language=language, voice=voice)
    if metrics is not None:
        metrics.tts_ms += (time.perf_counter() - tts_start) * 1000

    if audio_bytes:
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        await websocket.send_json({"type": "audio", "data": audio_b64})

async def stream_response_with_tts(
    websocket: WebSocket,
    llm_stream,
    session_id: str = None,
    language: str = "en-US",
    voice: str = None,
    sentiment_score: float = None,
    sent_tracker: list = None,
    metrics: TurnMetrics = None,
):
    """Stream LLM response with sentence-buffered TTS."""
    full_response = ""
    current_sentence = ""
    
    async for chunk in llm_stream:
        full_response += chunk
        current_sentence += chunk
        if sent_tracker is not None:
            sent_tracker.append(chunk)
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

                tts_start = time.perf_counter()
                if 'instruct' in inspect.signature(tts_service.synthesize).parameters:
                    audio_bytes = await tts_service.synthesize(current_sentence, language=language, voice=voice, instruct=instruct)
                else:
                    audio_bytes = await tts_service.synthesize(current_sentence, language=language, voice=voice)
                if metrics is not None:
                    metrics.tts_ms += (time.perf_counter() - tts_start) * 1000
                    
                if audio_bytes:
                    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                    await websocket.send_json({"type": "audio", "data": audio_b64})
                current_sentence = ""
    
    # Flush remaining
    if len(current_sentence.strip()) > 2:
        instruct = None
        if sentiment_score is not None:
            if sentiment_score < 0.3: instruct = "empathetic, soft"
            elif sentiment_score > 0.8: instruct = "excited"
            else: instruct = "professional"

        tts_start = time.perf_counter()
        if 'instruct' in inspect.signature(tts_service.synthesize).parameters:
            audio_bytes = await tts_service.synthesize(current_sentence, language=language, voice=voice, instruct=instruct)
        else:
            audio_bytes = await tts_service.synthesize(current_sentence, language=language, voice=voice)
        if metrics is not None:
            metrics.tts_ms += (time.perf_counter() - tts_start) * 1000

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

class TurnProcessor:
    """Manages the full state, lifecycle, and turn execution for a single active WebSocket agent session."""
    def __init__(
        self,
        db: Session,
        websocket: WebSocket,
        agent: models.Agent,
        agent_id: str,
        session_id: str,
        caller_id: Optional[str] = None,
        org_id: Optional[str] = None,
        session_language: str = "en-US",
        session_voice: str = "auto",
        active_persona: str = "",
        active_tools: List = None,
        tool_schemas: Any = None,
        session_policy: Any = None,
    ):
        self.db = db
        self.websocket = websocket
        self.agent = agent
        self.agent_id = agent_id
        self.session_id = session_id
        self.caller_id = caller_id
        self.org_id = org_id
        self.session_language = session_language
        self.session_voice = session_voice
        self.active_persona = active_persona
        self.active_tools = active_tools or []
        self.tool_schemas = tool_schemas
        self.session_policy = session_policy

        # Initialize core services
        self.orchestrator = AgentOrchestrator(db, policy=session_policy)
        self.llm_service = EnterpriseLLM(primary_model="llama-3.3-70b-versatile")
        self.memory_service = get_memory_service(db)
        self.analytics_service = AnalyticsService(db)
        self.voice_ux = VoiceUXService(tts_service)
        self.shadow_service = ShadowComparisonService(db)

        # Phase 8: Emotional tracking
        self.emotion_tracker = EmotionTracker(window_size=5)

        # Phase 8: End-of-call intelligence
        self.end_of_call = EndOfCallService(db, llm_service=self.llm_service)

        # Phase 8: Cost tracking
        self.current_model_name = "llama-3.3-70b-versatile"
        self.cost_per_1m_input = MODEL_COST_RATES.get(self.current_model_name, 0.59)

        # Context setup
        now = datetime.utcnow()
        user_context = ""
        self.context = AgentContext(
            session_id=session_id,
            caller_id=self.caller_id,
            history=[],
            current_intent=None,
            extracted_info={},
            current_state=session_policy.initial_state if session_policy else "GREETING",
            confidence=ConfidenceScores(),
            memory=[],
            sentiment_slope=0.8,
            call_started_at=now,
            metadata={"org_id": self.org_id}
        )

        # Tracking state
        self.session_start_dt = now
        self.latencies: List[float] = []
        self.turn_count = 0
        self.token_count = 0
        self._sent_buffer: list = []
        self._tracer = get_tracer("turn_processor")
        self._inter_agent_listener_task: Optional[asyncio.Task] = None

    async def initialize_context(self):
        """Asynchronously load memory context and checkpoint from database."""
        # Attempt crash recovery from latest checkpoint
        try:
            ckpt_service = CheckpointService(self.db)
            previous_state = ckpt_service.resume_state(self.session_id)
            if previous_state:
                history = previous_state.get("history", [])
                turn_count = previous_state.get("turn_count", 0)
                self.context.history = history
                self.turn_count = turn_count
                self.token_count = previous_state.get("token_count", 0)
                self.latencies = previous_state.get("latencies", [])
                if previous_state.get("current_state"):
                    self.context.current_state = previous_state["current_state"]
                logger.info(
                    f"Recovered session {self.session_id} from checkpoint "
                    f"(turn {turn_count}, {len(history)} messages)"
                )
        except Exception as e:
            logger.warning(f"Checkpoint recovery skipped (non-fatal): {e}")

        if self.caller_id:
            user_context = await self.memory_service.get_context_for_call(
                self.caller_id,
                organization_id=self.org_id,
                agent_id=self.agent_id
            )
            if user_context:
                self.context.memory = [user_context]
                logger.info(f"Loaded memory context for user {self.caller_id} (Org: {self.org_id}, Agent: {self.agent_id})")

        # Start InterAgentBus listener for this agent
        try:
            self._inter_agent_listener_task = asyncio.create_task(
                self._listen_inter_agent_messages()
            )
            logger.info(f"InterAgentBus listener started for agent {self.agent_id}")
        except Exception as e:
            logger.warning(f"InterAgentBus listener failed to start (non-fatal): {e}")

    async def _listen_inter_agent_messages(self):
        """Listen for inter-agent messages from the bus."""
        async def handler(message: dict):
            msg_type = message.get("type")
            if msg_type == "task_delegation":
                task = message.get("payload", {}).get("task", "")
                logger.info(f"InterAgentBus: received task delegation: {task}")
            elif msg_type == "agent_hired":
                hired_by = message.get("payload", {}).get("by", "unknown")
                task = message.get("payload", {}).get("task", "")
                logger.info(f"InterAgentBus: hired by {hired_by} for task: {task}")
            return None  # No reply needed for fire-and-forget

        await inter_agent_bus.listen(self.agent_id, handler)

    def is_fast_path_turn(self, text: str) -> Optional[str]:
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

    async def _emit_turn_metrics(self, metrics: TurnMetrics) -> None:
        turn_latency_ms.labels(phase="stt").observe(metrics.stt_ms)
        turn_latency_ms.labels(phase="understand").observe(metrics.understand_ms)
        turn_latency_ms.labels(phase="llm").observe(metrics.llm_ms)
        turn_latency_ms.labels(phase="tool").observe(metrics.tool_ms)
        turn_latency_ms.labels(phase="tts").observe(metrics.tts_ms)
        turn_latency_ms.labels(phase="total").observe(metrics.total_ms)
        payload = metrics.to_dict()
        logger.info(f"turn_metrics {json.dumps(payload)}")
        await self.websocket.send_json({"type": "turn_metrics", **payload})
        await monitoring_service.broadcast_event(self.session_id, "turn_metrics", payload)

    async def process_turn(
        self,
        user_input: str,
        stt_confidence: float = 1.0,
        stt_ms: float = 0.0,
    ):
        """Process a single turn of conversation."""
        async with async_trace_span(self._tracer, "turn_processor.process_turn", {
            "session_id": self.session_id,
            "turn_index": self.turn_count + 1,
            "agent_id": self.agent_id,
            "stt_confidence": stt_confidence,
        }):
            turn_start = time.perf_counter()
        self.turn_count += 1
        metrics = TurnMetrics(
            session_id=self.session_id,
            turn_index=self.turn_count,
            stt_provider=settings.STT_PROVIDER,
            stt_ms=stt_ms,
            confidence_vector={"stt": stt_confidence},
        )
        understand_start = time.perf_counter()
        llm_start: Optional[float] = None
        response_path = "standard"

        try:
            # Reset sent buffer for this turn
            self._sent_buffer = []
            
            # Phase 8: Multi-Signal Emotional Tracking
            current_sentiment = self.orchestrator.analyze_sentiment(user_input)
            self.context.sentiment_slope = (self.context.sentiment_slope * 0.7) + (current_sentiment * 0.3)

            emotion_state = self.emotion_tracker.analyze_turn(
                text=user_input,
                silence_duration=self.context.silence_accumulated_seconds,
                interrupt_frequency=(
                    self.context.interrupt_count / max(1, self.turn_count)
                ),
                turn_cadence=(
                    self.context.call_elapsed_seconds / max(1, self.turn_count)
                ),
            )
            self.context.frustration_level = emotion_state.frustration_level
            self.context.emotion_history.append({
                "turn": self.turn_count,
                "state": emotion_state.to_dict(),
            })
            self.context.hesitation_markers += (
                1 if emotion_state.hesitation_level > 0.4 else 0
            )

            # 2. Fast Path Check (Elite Feature)
            fast_response = self.is_fast_path_turn(user_input)
            if fast_response:
                logger.info("Fast Path Triggered")
                metrics.path = "fast_path"
                metrics.understand_ms = (time.perf_counter() - understand_start) * 1000
                await send_with_tts(
                    self.websocket, fast_response,
                    language=self.session_language, voice=self.session_voice,
                    sentiment_score=self.context.sentiment_slope,
                    sent_tracker=self._sent_buffer, metrics=metrics,
                )
                await session_manager.add_to_history(self.session_id, "user", user_input)
                await session_manager.add_to_history(self.session_id, "assistant", fast_response)
                metrics.total_ms = (time.perf_counter() - turn_start) * 1000
                await self._emit_turn_metrics(metrics)
                await self.websocket.send_json({"type": "end_response"})
                return

            # 3. Check for HITL Intervention
            hitl_service = HITLService(self.db)
            intervention = await hitl_service.get_intervention_status(self.session_id)
            
            # CASE A: HUMAN TAKEOVER
            if intervention and intervention.mode == "takeover":
                logger.info(f"Session {self.session_id} in TAKEOVER mode.")
                await monitoring_service.broadcast_event(self.session_id, "hitl_takeover", {"active": True, "agent": intervention.user_id})
                
                # Fetch supervisor responses from human input queue (handled in the main loop)
                raise RuntimeError("Takeover state must yield to human input queue")

            # Broadcast user transcription to monitoring
            await monitoring_service.broadcast_event(self.session_id, "transcription", {
                "text": user_input,
                "role": "user"
            })
            
            # Voice UX: Micro-acknowledgement for longer inputs (Elite Feature)
            if len(user_input.split()) > 10:
                # Send a quick "mm-hm" or "Right" to signal the user was heard
                await self.voice_ux.send_backchannel(self.websocket)
            
            # 3. Policy Engine: Input Guard & State Transition
            intent_name, intent_confidence = self.orchestrator.detect_intent(user_input)
            self.context.current_intent = intent_name
            
            # Confidence Check (Elite Feature)
            # STT confidence comes from the websocket frame payload; intent from detection
            self.context.confidence.stt = stt_confidence
            self.context.confidence.intent = intent_confidence
            self.context.confidence.overall = (self.context.confidence.stt + self.context.confidence.intent) / 2
            metrics.confidence_vector = {
                "stt": self.context.confidence.stt,
                "intent": self.context.confidence.intent,
                "overall": self.context.confidence.overall,
            }
            
            # Handle Low Confidence Early
            confidence_response = self.orchestrator.handle_low_confidence(self.context)
            if confidence_response:
                logger.warning(f"Low Confidence handoff triggered: {self.context.confidence.overall}")
                metrics.path = "clarify"
                metrics.understand_ms = (time.perf_counter() - understand_start) * 1000
                await send_with_tts(
                    self.websocket, confidence_response,
                    language=self.session_language, voice=self.session_voice,
                    sentiment_score=self.context.sentiment_slope, metrics=metrics,
                )
                metrics.total_ms = (time.perf_counter() - turn_start) * 1000
                await self._emit_turn_metrics(metrics)
                await self.websocket.send_json({"type": "end_response"})
                return

            if self.orchestrator.policy_engine:
                is_allowed, reason = self.orchestrator.policy_engine.validate_input(
                    self.context.current_state, user_input, self.context.current_intent
                )
                if not is_allowed:
                    metrics.path = "policy_blocked"
                    metrics.policy_blocked = True
                    metrics.understand_ms = (time.perf_counter() - understand_start) * 1000
                    await send_with_tts(
                        self.websocket, f"I'm sorry, I cannot process that request. {reason}",
                        language=self.session_language, voice=self.session_voice,
                        sentiment_score=self.context.sentiment_slope, metrics=metrics,
                    )
                    metrics.total_ms = (time.perf_counter() - turn_start) * 1000
                    await self._emit_turn_metrics(metrics)
                    await self.websocket.send_json({"type": "end_response"})
                    return
                
                self.context.current_state = self.orchestrator.policy_engine.get_next_state(self.context.current_state, "user_spoke")
                if self.context.current_intent:
                    self.context.current_state = self.orchestrator.policy_engine.get_next_state(self.context.current_state, f"{self.context.current_intent}_intent")

            # 4. Agent Selection (Dynamic Swarm Routing)
            swarm = SwarmOrchestrator(self.db, self.agent)
            available_specialists = self.orchestrator.get_agents_by_role("specialist")
            
            # Elite feature: if supervisor, route to specialist
            if self.agent.role == "supervisor" or "swarm" in (self.agent.description or "").lower():
                selected_agent = await swarm.route_task(user_input, self.context.history, available_specialists)
                
                # PEAK AGENTIC FEATURE: Autonomous Discovery
                # If pool selection failed to find a worker, search the whole Org dynamically
                if selected_agent.id == self.agent.id:
                    discovered_agent = await swarm.discover_and_hire(user_input)
                    if discovered_agent:
                        selected_agent = discovered_agent
                        await self.websocket.send_json({
                            "type": "agent_discovery",
                            "name": discovered_agent.name,
                            "capability": user_input[:50]
                        })

                if selected_agent.id != self.agent.id:
                    await self.websocket.send_json({
                        "type": "agent_switch",
                        "from": self.agent.name, "to": selected_agent.name,
                        "reason": "Swarm Delegation"
                    })
                    self.agent = selected_agent
            else:
                # Standard routing
                selected_agent = await self.orchestrator.select_agent(self.context, self.agent_id)
                if selected_agent.id != self.agent.id:
                    self.agent = selected_agent
            
            # PEAK AGENTIC FEATURE: Knowledge Retrieval (RAG)
            knowledge_context = ""
            knowledge_service = KnowledgeService(self.db)
            relevant_chunks = await knowledge_service.query_knowledge(self.agent.id, user_input, limit=2)
            
            if relevant_chunks:
                logger.info(f"RAG: Found {len(relevant_chunks)} relevant knowledge chunks.")
                knowledge_context = "\n\nUSE THESE FACTS FROM YOUR KNOWLEDGE BASE IF RELEVANT:\n" + \
                                    "\n".join([f"- {c['content']}" for c in relevant_chunks])
                await self.websocket.send_json({"type": "knowledge_hit", "count": len(relevant_chunks)})

            metrics.understand_ms = (time.perf_counter() - understand_start) * 1000

            # 5. Response Generation (AI or Whisper)
            full_response = ""
            response_sent = False
            LATENCY_BUDGET = 2.5 # Max seconds for reasoning path before we degrade UX
            llm_start = time.perf_counter()
            
            # CASE B: WHISPER MODE
            if intervention and intervention.mode == "whisper":
                logger.info(f"Session {self.session_id} in WHISPER mode. Generating suggestion for supervisor.")
                
                # Generate a quick suggestion (non-streaming for speed)
                suggestion_prompt = f"{self.active_persona}{knowledge_context}\n\nSUGGESTION MODE: Provide a concise response for the supervisor to use."
                suggestion = await self.llm_service.generate_response(user_input, suggestion_prompt, self.context.history)
                
                # Broadcast suggestion to supervisor console
                await monitoring_service.broadcast_event(self.session_id, "whisper_suggestion", {
                    "suggestion": suggestion,
                    "original_input": user_input
                })
                
                # Yield and wait for supervisor response in the main loop
                raise RuntimeError("Whisper state must yield to human input queue")
            
            # NORMAL AI RESPONSE
            if not full_response:
                # Inject memory context into prompt
                memory_context = ""
                if self.context.memory:
                    memory_context = f"\n\n**Caller Context:**\n" + "\n".join(self.context.memory)

                # Phase 8: Time-awareness — inject remaining budget into prompt
                time_context = ""
                if self.context.is_near_call_end:
                    time_context = "\n\nNOTE: This call is almost over. Keep responses short and avoid introducing new topics."
                elif self.context.call_elapsed_seconds > self.context.call_duration_budget_seconds * 0.7:
                    time_context = "\n\nNOTE: The call is running long. Aim for concise responses."

                # Phase 8: Emotional adaptation — inject tone guidance
                emotion_hint = self.emotion_tracker.get_adaptation_hint()
                tone_context = f"\n\nTone: {emotion_hint['tone']}. Pace: {emotion_hint['pace']}."

                system_prompt = f"{self.active_persona}{memory_context}{knowledge_context}{time_context}{tone_context}\n\nIMPORTANT: Respond only in {self.session_language}."
                await session_manager.set_floor_owner(self.session_id, "agent")
                await self.websocket.send_json({"type": "start_response"})
                
                # Phase 8: Cost-aware model downgrade with real-time cost calc
                self.context.tokens_used = self.token_count
                # Estimate cost: input ~70% of total tokens
                estimated_input_tokens = int(self.token_count * 0.7)
                estimated_cost = (estimated_input_tokens / 1_000_000) * self.cost_per_1m_input
                self.context.estimated_cost = estimated_cost

                if self.context.is_exceeding_cost_budget:
                    logger.warning(
                        f"COST BUDGET EXCEEDED (${estimated_cost:.4f} / ${self.context.cost_budget:.2f}). "
                        f"Switching to fallback: {self.agent.fallback_model}"
                    )
                    self.llm_service.model = self.agent.fallback_model or "llama-3.1-8b-instant"
                    self.cost_per_1m_input = MODEL_COST_RATES.get(self.llm_service.model, 0.18)
                elif self.token_count > (self.agent.token_limit or 50000) * 0.75:
                    logger.info(f"APPROACHING TOKEN LIMIT ({self.token_count}). Pre-emptive model downgrade.")
                    self.llm_service.model = self.agent.fallback_model or "llama-3.1-8b-instant"
                    self.cost_per_1m_input = MODEL_COST_RATES.get(self.llm_service.model, 0.18)

                try:
                    # Voice UX: Send a "filler" if we expect a long reasoning path
                    is_reasoning_path = "multi-agent" in (self.agent.description or "").lower() or self.tool_schemas is not None
                    if is_reasoning_path:
                        # Send a random filler to bridge the latency gap
                        await self.voice_ux.send_filler(self.websocket)

                    # Enforce Latency Budget per Step
                    # Check for LangGraph (Complex Reasoning Path)
                    if "multi-agent" in (self.agent.description or "").lower():
                        response_path = "langgraph"
                        from app.orchestration.langgraph_orchestrator import LangGraphOrchestrator
                        lg_orchestrator = LangGraphOrchestrator(agent_id=self.agent_id, session_id=self.session_id, language=self.session_language)
                        full_response = await asyncio.wait_for(
                            lg_orchestrator.get_response(user_input, self.context.history),
                            timeout=LATENCY_BUDGET
                        )
                    
                    # Strategic Tool Planning (Elite Feature)
                    elif self.tool_schemas and hasattr(self.llm_service, 'generate_with_tools'):
                        response_path = "tools"
                        planner = get_tool_planner()
                        plan_statement, tool_calls = await planner.generate_plan(user_input, self.context.history, self.tool_schemas)
                        
                        if plan_statement:
                            await send_with_tts(
                                self.websocket, plan_statement,
                                language=self.session_language, voice=self.session_voice,
                                sentiment_score=self.context.sentiment_slope,
                                sent_tracker=self._sent_buffer, metrics=metrics,
                            )
                            logger.info(f"Speaking Plan: {plan_statement}")
                        
                        if not tool_calls:
                            t0 = time.perf_counter()
                            text_response, tool_calls = await asyncio.wait_for(
                                self.llm_service.generate_with_tools(user_input, system_prompt, self.context.history, tools=self.tool_schemas),
                                timeout=LATENCY_BUDGET
                            )
                            persist_span(self.session_id, "llm.generate_with_tools", "llm",
                                (time.perf_counter() - t0) * 1000,
                                {"model": self.llm_service.model, "agent_id": self.agent_id},
                                agent_id=self.agent_id, organization_id=self.org_id)
                        
                        if tool_calls:
                            if self.orchestrator.policy_engine:
                                self.context.current_state = self.orchestrator.policy_engine.get_next_state(self.context.current_state, "tool_needed")
                            
                            tool_results = []
                            for tc in tool_calls:
                                tool_start = time.perf_counter()
                                await self.websocket.send_json({"type": "tool_call", "name": tc.get("name"), "arguments": tc.get("arguments", {})})
                                result_dict = await execute_tool(tc.get("name", ""), tc.get("arguments", {}), self.db, self.agent_id, self.session_id)
                                tool_elapsed = (time.perf_counter() - tool_start) * 1000
                                metrics.tool_ms += tool_elapsed
                                persist_span(self.session_id, f"tool.{tc.get('name')}", "tool",
                                    tool_elapsed, {"tool_name": tc.get("name"), "confidence": result_dict.get("confidence")},
                                    agent_id=self.agent_id, organization_id=self.org_id)
                                tool_results.append(result_dict)
                                
                                # Update context confidence from tool result
                                if not result_dict.get("error") and result_dict.get("confidence", 1.0) < 0.5:
                                    self.context.confidence.tool_result = result_dict["confidence"]
                            
                            if self.orchestrator.policy_engine:
                                self.context.current_state = self.orchestrator.policy_engine.get_next_state(self.context.current_state, "tool_complete")
                            
                            tool_context = "\n".join([f"[Tool: {tr.get('name')}] Result: {tr.get('result', '')}" for tr in tool_results])
                            full_response = await stream_response_with_tts(
                                self.websocket,
                                self.llm_service.generate_stream(f"Based on: {tool_context}", system_prompt, self.context.history),
                                self.session_id, language=self.session_language, voice=self.session_voice,
                                sentiment_score=self.context.sentiment_slope,
                                sent_tracker=self._sent_buffer, metrics=metrics,
                            )
                            response_sent = True
                        else:
                            full_response = text_response
                    
                    # Default Stream
                    else:
                        response_path = "standard_stream"
                        t0 = time.perf_counter()
                        full_response = await stream_response_with_tts(
                            self.websocket,
                            self.llm_service.generate_stream(user_input, system_prompt, self.context.history),
                            self.session_id, language=self.session_language, voice=self.session_voice,
                            sentiment_score=self.context.sentiment_slope,
                            sent_tracker=self._sent_buffer, metrics=metrics,
                        )
                        persist_span(self.session_id, "llm.generate_stream", "llm",
                            (time.perf_counter() - t0) * 1000,
                            {"model": self.llm_service.model, "agent_id": self.agent_id},
                            agent_id=self.agent_id, organization_id=self.org_id)
                        response_sent = True

                except asyncio.TimeoutError:
                    response_path = "degraded"
                    logger.warning(f"LATENCY BUDGET EXCEEDED ({LATENCY_BUDGET}s). Entering Degradation Mode.")
                    full_response = "I'm looking into that for you. One moment please..."
                    await send_with_tts(
                        self.websocket, full_response,
                        language=self.session_language, voice=self.session_voice,
                        sentiment_score=self.context.sentiment_slope,
                        sent_tracker=self._sent_buffer, metrics=metrics,
                    )
                    response_sent = True
                finally:
                    if llm_start is not None:
                        metrics.llm_ms = (time.perf_counter() - llm_start) * 1000

            # 6. Policy Engine: Output Guard
            if self.orchestrator.policy_engine:
                is_valid, validated_text = self.orchestrator.policy_engine.validate_response(self.context.current_state, full_response)
                
                # Dynamic Security: Critical states trigger inline compliance audit
                state_config = self.session_policy.states.get(self.context.current_state)
                if state_config and state_config.is_sensitive:
                    logger.info(f"Inline Compliance Audit triggered for sensitive state: {self.context.current_state}")
                    rules = get_baseline_rules(db=self.db, organization_id=self.org_id)
                    audit_result = await compliance_validator.validate_turn(user_input, validated_text, rules, self.turn_count)
                    
                    if not audit_result.is_compliant:
                        logger.warning(f"CRITICAL COMPLIANCE VIOLATION in sensitive state: {audit_result.risk_score}")
                        validated_text = "I'm sorry, I cannot fulfill that request due to regulatory constraints."
                        if any(v.severity == "critical" for v in audit_result.violations):
                            await self.websocket.send_json({"type": "compliance_alert", "risk_score": audit_result.risk_score})
                
                full_response = validated_text

            # 7. Final Delivery (if not streamed)
            if full_response and not response_sent:
                # PEAK AGENTIC FEATURE: Self-Correction Loop (use fast model for performance)
                fast_llm_model = self.llm_service
                if hasattr(self.llm_service, 'model'):
                    original_model = self.llm_service.model
                    self.llm_service.model = "llama-3.1-8b-instant"
                full_response = await self.orchestrator.reflect_and_correct(
                    user_input, full_response, self.context, self.agent, fast_llm_model
                )
                if hasattr(self.llm_service, 'model'):
                    self.llm_service.model = original_model
                await send_with_tts(self.websocket, full_response, language=self.session_language, voice=self.session_voice, sentiment_score=self.context.sentiment_slope, sent_tracker=self._sent_buffer)

            # 8. Escalation & History
            should_escalate, reason = await self.orchestrator.should_escalate(self.context, full_response, self.agent, self.llm_service)
            if should_escalate:
                await session_manager.escalate_session(self.session_id, reason)
                await send_with_tts(self.websocket, "One moment, transferring you to a specialist.", language=self.session_language, voice=self.session_voice, sentiment_score=self.context.sentiment_slope, sent_tracker=self._sent_buffer)
                return "ESCALATED"
            
            await session_manager.add_to_history(self.session_id, "user", user_input)
            await session_manager.add_to_history(self.session_id, "assistant", full_response)
            self.context.history.append({"role": "user", "content": user_input})
            self.context.history.append({"role": "assistant", "content": full_response})
            
            latency = (time.perf_counter() - turn_start) * 1000
            self.latencies.append(latency)
            metrics.path = response_path
            metrics.total_ms = latency
            await self._emit_turn_metrics(metrics)
            await session_manager.set_floor_owner(self.session_id, "user")
            
            # Update Token Count
            turn_tokens = int((len(user_input.split()) + len(full_response.split())) * 1.3)
            self.token_count += turn_tokens
            self.context.tokens_used = self.token_count

            # Phase 8: Real-time cost estimation
            estimated_input_tokens = int(self.token_count * 0.7)
            self.context.estimated_cost = (
                estimated_input_tokens / 1_000_000
            ) * self.cost_per_1m_input

            # Durable checkpoint — save after every completed turn
            try:
                ckpt_service = CheckpointService(self.db)
                ckpt_service.save(
                    session_id=self.session_id,
                    agent_id=self.agent_id,
                    turn_index=self.turn_count,
                    state={
                        "history": self.context.history,
                        "current_state": self.context.current_state,
                        "turn_count": self.turn_count,
                        "token_count": self.token_count,
                        "latencies": self.latencies,
                        "sentiment_slope": getattr(self.context, "sentiment_slope", None),
                    },
                    summary=full_response[:200] if full_response else None,
                )
            except Exception as e:
                logger.warning(f"Checkpoint save failed (non-fatal): {e}")
            logger.info(f"Turn Tokens: {turn_tokens}, Total Session Tokens: {self.token_count}")
            
            # 9. Compliance & Audit (Shadow Audit)
            # Use Background task to not block the voice turn - Thread & Task Safe
            async def run_compliance_audit_bg():
                from app.core.database import SessionLocal
                from fastapi.concurrency import run_in_threadpool
                
                def fetch_rules():
                    with SessionLocal() as local_db:
                        return get_baseline_rules(db=local_db, organization_id=self.org_id)
                
                try:
                    rules = await run_in_threadpool(fetch_rules)
                    audit_result = await compliance_validator.validate_turn(
                        user_input, full_response, rules, self.turn_count
                    )
                    
                    def save_audit():
                        with SessionLocal() as local_db:
                            audit_service = AuditService(local_db)
                            audit_service.append(
                                session_id=self.session_id,
                                agent_id=self.agent_id,
                                turn_index=self.turn_count,
                                user_message=redactor.redact_text(user_input),
                                ai_response=redactor.redact_text(full_response),
                                is_compliant=audit_result.is_compliant,
                                violations=[v.dict() for v in audit_result.violations],
                                risk_score=audit_result.risk_score,
                                organization_id=self.org_id,
                                state_name=self.context.current_state,
                            )
                            
                    await run_in_threadpool(save_audit)
                    
                    if not audit_result.is_compliant:
                        await monitoring_service.broadcast_event(self.session_id, "compliance_alert", {
                            "severity": "critical",
                            "violations": [v.rule_name for v in audit_result.violations]
                        })
                except Exception as audit_err:
                    logger.error(f"Background compliance audit failed: {audit_err}")

            asyncio.create_task(run_compliance_audit_bg())

            # 10. Shadow Comparison (Elite Feature)
            # Execute background comparison safely without DB session conflicts
            asyncio.create_task(self.shadow_service.compare_turn(
                session_id=self.session_id,
                turn_index=self.turn_count,
                user_input=user_input,
                system_prompt=self.active_persona,
                history=self.context.history,
                primary_response=full_response,
                primary_model_name="groq-llama-3-3-70b",
                primary_latency=latency,
                organization_id=self.org_id,
                tools=self.tool_schemas if is_reasoning_path else None
            ))
            
            # Record turn span in persistent storage
            persist_span(self.session_id, "turn", "turn", latency,
                {"turn_index": self.turn_count, "path": response_path,
                 "tokens": turn_tokens, "confidence": metrics.confidence_vector.get("overall", 0)},
                agent_id=self.agent_id, organization_id=self.org_id)
            
            await self.websocket.send_json({"type": "end_response"})
            logger.info(f"Turn {self.turn_count} complete. Latency: {latency:.2f}ms. Compliance: {len(self.latencies)}")

        except asyncio.CancelledError:
            metrics.barge_in = True
            metrics.total_ms = (time.perf_counter() - turn_start) * 1000
            await self._emit_turn_metrics(metrics)
            sent_text = "".join(self._sent_buffer).strip()
            logger.info(f"Response generation cancelled (Barge-In). Sent text: {sent_text[:100]}")
            if sent_text:
                await session_manager.add_to_history(self.session_id, "assistant", sent_text)
                self.context.history.append({"role": "assistant", "content": sent_text})
            await session_manager.set_floor_owner(self.session_id, "user")
            raise
        except Exception as e:
            correlation_id = str(uuid.uuid4())[:8]
            logger.exception(f"Error in turn [CID: {correlation_id}]: {e}")
            errors_total.labels(error_type=type(e).__name__, source="turn_processor").inc()
            await self.websocket.send_json({
                "type": "error", 
                "message": f"An error occurred while generating the response. Reference: {correlation_id}"
            })

    async def log_session_completion(self):
        """Clean up and record session metrics at completion."""
        try:
            avg_lat = sum(self.latencies)/len(self.latencies) if self.latencies else 0
            duration = (datetime.utcnow() - self.session_start_dt).total_seconds()
            await self.analytics_service.log_call_completion({
                "session_id": self.session_id,
                "agent_id": self.agent_id,
                "caller_id": self.caller_id,
                "start_time": self.session_start_dt,
                "duration": duration,
                "avg_latency": avg_lat,
                "turns": self.turn_count,
                "tokens": self.token_count,
                "cost": round(self.context.estimated_cost, 4),
                "model_name": self.current_model_name,
                "org_id": self.org_id,
                "status": "completed",
                "transcript": self.context.history
            }, agent=self.agent)

            # Phase 8: End-of-Call Intelligence
            call_summary = await self.end_of_call.analyze(
                transcript=self.context.history,
                context=self.context,
                agent=self.agent,
            )
            await self.end_of_call.save_to_db(
                session_id=self.session_id,
                agent_id=self.agent_id,
                caller_id=self.caller_id,
                summary=call_summary,
                organization_id=self.org_id,
            )

            # Post-Call Memory Governance
            if self.caller_id:
                # 1. Summarize
                await self.memory_service.summarize_conversation(
                    session_id=self.session_id,
                    user_id=self.caller_id,
                    agent_id=self.agent_id,
                    conversation=self.context.history,
                    outcome=self.agent.success_criteria[0] if self.agent.success_criteria else "unknown",
                    llm_service=self.llm_service,
                    organization_id=self.org_id
                )
                # 2. Extract specific fact memories
                await self.memory_service.memorize_from_conversation(
                    user_id=self.caller_id,
                    conversation=self.context.history,
                    agent_id=self.agent_id,
                    session_id=self.session_id,
                    llm_service=self.llm_service,
                    organization_id=self.org_id
                )

            # Clear working memory for this session
            await self.memory_service.clear_working(self.session_id)

            if self._inter_agent_listener_task and not self._inter_agent_listener_task.done():
                self._inter_agent_listener_task.cancel()
            await session_manager.end_session(self.session_id, "client_disconnect")
        except Exception as e:
            logger.error(f"Cleanup Error: {e}")
