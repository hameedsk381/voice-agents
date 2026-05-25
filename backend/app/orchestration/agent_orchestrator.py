"""
Multi-agent orchestration system.
Supports supervisor-worker patterns and dynamic agent routing.
"""
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from loguru import logger
from app.models.agent import Agent
from sqlalchemy.orm import Session
from app.orchestration.policy_engine import PolicyEngine
from app.schemas.policy import ConversationPolicy


class AgentRole(str, Enum):
    """Types of agent roles in orchestration."""
    PRIMARY = "primary"         # Main agent handling the call
    SUPERVISOR = "supervisor"   # Oversees other agents
    SPECIALIST = "specialist"   # Handles specific domain
    VALIDATOR = "validator"     # Validates responses
    FALLBACK = "fallback"       # Backup agent

class MemoryType(str, Enum):
    """Categories of information for the Truth Layer."""
    USER_CLAIM = "user_claim"             # Unverified info from user
    SYSTEM_VERIFIED = "system_verified"   # Verified by tools/logic
    REGULATED_FACT = "regulated_fact"     # Static industry knowledge
    ASSUMPTION = "assumption"             # LLM derived assumption
    TEMP_CONTEXT = "temp_context"         # Only valid for this turn

@dataclass
class MemoryItem:
    """A granular piece of information in the context."""
    key: str
    value: Any
    type: MemoryType = MemoryType.USER_CLAIM
    confidence: float = 1.0
    verified_at: Optional[str] = None

@dataclass
class ConfidenceScores:
    """Confidence levels across the pipeline layers."""
    stt: float = 1.0
    intent: float = 1.0
    policy: float = 1.0
    llm_response: float = 1.0
    tool_result: float = 1.0
    overall: float = 1.0

    # Configurable thresholds
    threshold_low: float = 0.4
    threshold_medium: float = 0.7

    def get_tier(self) -> str:
        if self.overall < self.threshold_low:
            return "low"
        if self.overall < self.threshold_medium:
            return "medium"
        return "high"

    def update_overall(self):
        self.overall = (
            self.stt * 0.30 +
            self.intent * 0.25 +
            self.policy * 0.10 +
            self.llm_response * 0.15 +
            self.tool_result * 0.20
        )


@dataclass
class AgentContext:
    """Context passed between agents."""
    session_id: str
    caller_id: Optional[str]
    history: List[Dict[str, str]]
    current_intent: Optional[str]
    extracted_info: Dict[str, Any]
    current_state: str = "initial"
    
    # Phase 6: Memory
    confidence: ConfidenceScores = field(default_factory=ConfidenceScores)
    memory: List[MemoryItem] = None
    sentiment_slope: float = 1.0
    
    # Phase 8: Time Awareness
    call_started_at: Optional[datetime] = None
    call_duration_budget_seconds: float = 600.0  # 10 min default
    silence_accumulated_seconds: float = 0.0
    was_interrupted: bool = False
    interrupt_count: int = 0
    
    # Phase 8: Cost Awareness
    tokens_used: int = 0
    estimated_cost: float = 0.0
    cost_budget: float = 0.50  # $0.50 default per call
    
    # Phase 8: Emotional State
    emotion_history: List[Dict[str, Any]] = field(default_factory=list)
    frustration_level: float = 0.0
    hesitation_markers: int = 0
    
    escalation_needed: bool = False
    escalation_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.memory is None:
            self.memory = []

    @property
    def call_elapsed_seconds(self) -> float:
        if not self.call_started_at:
            return 0.0
        return (datetime.utcnow() - self.call_started_at).total_seconds()

    @property
    def remaining_time_budget(self) -> float:
        return max(0.0, self.call_duration_budget_seconds - self.call_elapsed_seconds)

    @property
    def is_near_call_end(self) -> bool:
        return self.remaining_time_budget < 60.0  # Less than 1 min left

    @property
    def remaining_cost_budget(self) -> float:
        return max(0.0, self.cost_budget - self.estimated_cost)

    @property
    def is_exceeding_cost_budget(self) -> bool:
        return self.estimated_cost >= self.cost_budget


class AgentOrchestrator:
    """
    Orchestrates multiple agents in a conversation.
    Handles routing, fallback, and escalation logic.
    """
    
    def __init__(self, db: Session, policy: Optional[ConversationPolicy] = None):
        self.db = db
        self.agent_cache: Dict[str, Agent] = {}
        self.policy_engine = PolicyEngine(policy) if policy else None
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent from cache or database."""
        if agent_id not in self.agent_cache:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if agent:
                self.agent_cache[agent_id] = agent
        return self.agent_cache.get(agent_id)
    
    def get_agents_by_role(self, role: str) -> List[Agent]:
        """Get all agents with a specific role."""
        return self.db.query(Agent).filter(Agent.role == role, Agent.is_active == True).all()
    
    async def select_agent(
        self, 
        context: AgentContext, 
        primary_agent_id: str
    ) -> Agent:
        """
        Select the best agent for the current context.
        May route to specialist or escalate to supervisor.
        """
        primary = self.get_agent(primary_agent_id)
        
        if not primary:
            logger.error(f"Primary agent {primary_agent_id} not found")
            raise ValueError(f"Agent {primary_agent_id} not found")
        
        # Check if we need escalation
        if context.escalation_needed:
            supervisor = self._find_supervisor(primary)
            if supervisor:
                logger.info(f"Escalating from {primary.name} to supervisor {supervisor.name}")
                return supervisor
        
        # Check if we should route to a specialist
        if context.current_intent:
            specialist = self._find_specialist(context.current_intent)
            if specialist and specialist.id != primary.id:
                logger.info(f"Routing to specialist {specialist.name} for intent: {context.current_intent}")
                return specialist
        
        return primary
    
    def _find_supervisor(self, agent: Agent) -> Optional[Agent]:
        """Find a supervisor agent."""
        supervisors = self.get_agents_by_role("supervisor")
        if supervisors:
            return supervisors[0]  # Simple: return first available
        return None
    
    def _find_specialist(self, intent: str) -> Optional[Agent]:
        """Find a specialist for a specific intent."""
        # Map intents to roles
        intent_role_map = {
            "billing": "billing",
            "technical": "technical",
            "sales": "sales",
            "refund": "billing",
            "complaint": "support",
        }
        
        role = intent_role_map.get(intent.lower())
        if role:
            specialists = self.get_agents_by_role(role)
            if specialists:
                return specialists[0]
        return None
    
    def analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of user message using an extensible, negation-aware
        scoring engine. Handles phrase boundaries and word-level negations.
        """
        text_lower = text.lower().strip()
        if not text_lower:
            return 0.5

        # Negation words that flip the sentiment of the subsequent word
        negations = {"not", "no", "never", "none", "without", "n't"}
        
        positive_words = {"thank", "good", "great", "excellent", "happy", "yes", "correct", "perfect", "love", "awesome", "wonderful", "satisfied", "fine"}
        negative_words = {"bad", "angry", "frustrated", "wrong", "no", "stop", "terrible", "worst", "unhappy", "broke", "fail", "hate", "dissatisfied", "error"}

        words = [w.strip(".,?!;:") for w in text_lower.split()]
        words = [w for w in words if w]

        pos_score = 0
        neg_score = 0

        for i, word in enumerate(words):
            is_pos = word in positive_words
            is_neg = word in negative_words

            if is_pos or is_neg:
                # Check for negation in the preceding 2 words
                is_negated = False
                start = max(0, i - 2)
                for j in range(start, i):
                    if words[j] in negations or words[j].endswith("n't"):
                        is_negated = True
                        break
                
                if is_pos:
                    if is_negated:
                        neg_score += 1.2  # "not good" -> negative
                    else:
                        pos_score += 1.0
                elif is_neg:
                    if is_negated:
                        pos_score += 1.0  # "not bad" -> positive
                    else:
                        neg_score += 1.2

        if pos_score > neg_score:
            diff = pos_score - neg_score
            return min(1.0, 0.5 + (diff * 0.25))
        elif neg_score > pos_score:
            diff = neg_score - pos_score
            return max(0.0, 0.5 - (diff * 0.25))
        
        return 0.5

    async def should_escalate(
        self, context: AgentContext, response: str, agent: Agent,
        llm_service=None
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if the current context requires escalation.
        Uses LLM-based semantic evaluation when available for failure conditions
        and success criteria. Falls back to keyword matching if no LLM provided.
        Returns (should_escalate, reason).
        """
        # 1. Check Agent-Specific Failure Conditions (Elite Feature)
        failure_conditions = agent.failure_conditions or []
        last_user_msg = context.history[-1]["content"].lower() if context.history else ""
        
        if failure_conditions and llm_service:
            semantic_prompt = f"""
            You are a safety monitor. Determine if the user's message violates any failure condition.
            
            Failure Conditions:
            {chr(10).join(f'- {c}' for c in failure_conditions)}
            
            User Message: "{last_user_msg}"
            
            Does this message match ANY failure condition semantically? Reply with YES or NO only.
            """
            eval_result = await llm_service.generate_response(
                "Evaluate failure conditions.", semantic_prompt, []
            )
            if eval_result and eval_result.strip().upper().startswith("YES"):
                return True, f"Failure Condition Triggered (semantic): {failure_conditions[0]}"
        elif failure_conditions:
            for condition in failure_conditions:
                if condition.lower() in last_user_msg:
                    return True, f"Failure Condition Triggered: {condition}"

        # 2. Check Global Sentiment Slope
        if context.sentiment_slope < 0.3:
            return True, "Predictive Handoff: Consistently negative sentiment"

        # 3. Explicit request triggers (Standard)
        escalation_keywords = [
            "speak to a human", "transfer to agent", "manager", "supervisor", 
            "not satisfied", "complaint", "human person"
        ]
        
        for keyword in escalation_keywords:
            if keyword in last_user_msg:
                return True, f"User requested: {keyword}"
        
        # 4. Success Check (Exit if primary goal reached) - Semantic LLM evaluation
        success_criteria = agent.success_criteria or []
        if success_criteria and llm_service:
            semantic_prompt = f"""
            You are a goal verifier. Determine if the assistant's response achieves any success criteria.
            
            Success Criteria:
            {chr(10).join(f'- {c}' for c in success_criteria)}
            
            Assistant Response: "{response}"
            
            Does this response satisfy ANY success criteria semantically? Reply with YES or NO only.
            """
            eval_result = await llm_service.generate_response(
                "Evaluate success criteria.", semantic_prompt, []
            )
            if eval_result and eval_result.strip().upper().startswith("YES"):
                if "escalate" in (agent.exit_actions or []):
                    return True, f"Goal Reached (semantic). Handing off for finalization."
        elif success_criteria:
            for criteria in success_criteria:
                if criteria.lower() in response.lower():
                    if "escalate" in (agent.exit_actions or []):
                        return True, f"Goal Reached: {criteria}. Handing off for finalization."

        # 5. Repeated frustration / lack of progress
        if len(context.history) > 6:
            recent_user_msgs = [h["content"] for h in context.history[-6:] if h["role"] == "user"]
            if len(set(recent_user_msgs)) < len(recent_user_msgs) / 2:
                return True, "User repeating questions (possible frustration)"
        
        return False, None

    def handle_low_confidence(self, context: AgentContext) -> Optional[str]:
        """
        Produce a clarification or handoff when pipeline confidence is low.
        Uses configurable thresholds and supports low/medium/high tiers.
        """
        conf = context.confidence
        tier = conf.get_tier()

        if tier == "low":
            return "I'm sorry, I'm having trouble following our conversation. Let me transfer you to a human agent who can help."

        if tier == "medium":
            lowest_dim = min(
                ("speech recognition", conf.stt),
                ("intent detection", conf.intent),
                key=lambda x: x[1]
            )
            if conf.stt < conf.threshold_medium:
                return "I want to make sure I understood correctly — could you repeat that?"
            if context.current_intent:
                return f"If I understand correctly, you're asking about {context.current_intent}. Is that right?"
            return "Let me make sure I'm helping with the right thing. Could you clarify a bit more?"

        # High confidence — check individual dimensions
        if conf.stt < conf.threshold_medium:
            return "I apologize, but I didn't quite catch that. Could you please repeat that more slowly?"
        if conf.tool_result < 0.5:
            return "I'm having trouble looking that up right now. Let me try a different way."

        return None
    
    def detect_intent(self, user_message: str) -> tuple[Optional[str], float]:
        """
        Detect intent using an extensible, regex word-boundary based matcher.
        Returns (intent_name, confidence) where confidence reflects match strength:
          - 0.95 for strict word-boundary pattern match
          - 0.0 for no match
        """
        import re
        message_lower = " " + user_message.lower().strip() + " "
        
        intent_patterns = {
            "billing": [
                r"\bbill(s|ing)?\b", r"\bpay(ment|s|ing|ed)?\b", r"\bcharge(s|d|ing)?\b",
                r"\binvoice(s)?\b", r"\brefund(s|ed|ing)?\b", r"\bmoney\b", r"\bcard\b",
                r"\bcredit\b", r"\bcost\b"
            ],
            "technical": [
                r"\berror(s)?\b", r"\bnot\s+work(ing|s|ed)?\b", r"\bbroken\b", r"\bbug(s)?\b",
                r"\bissue(s)?\b", r"\bproblem(s)?\b", r"\bcrash(ed|es|ing)?\b", r"\bconnect(ion|s|ed)?\b",
                r"\bfail(s|ed|ure)?\b", r"\bfreeze\b", r"\bglitch\b"
            ],
            "sales": [
                r"\bbuy\b", r"\bpurchase\b", r"\bpricing\b", r"\bsubscribe\b", r"\bsign\s+up\b",
                r"\bplan(s)?\b", r"\bquote\b", r"\bdeal(s)?\b"
            ],
            "order": [
                r"\border(s|ed|ing)?\b", r"\bship(ping|ment|ped)?\b", r"\bdeliver(y|ies|ed)?\b",
                r"\btrack(ing|s|ed)?\b", r"\bpackage(s)?\b", r"\bitem(s)?\b"
            ],
            "account": [
                r"\baccount(s)?\b", r"\blogin\b", r"\blog\s+in\b", r"\bpassword(s)?\b",
                r"\bprofile\b", r"\bsetting(s)?\b", r"\buser(name|s)?\b", r"\bsign\s+in\b"
            ]
        }
        
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    logger.info(f"Intent detected: '{intent}' via pattern '{pattern}'")
                    return intent, 0.95
        
        # Loose keyword check for partial matches
        intent_loose_keywords = {
            "billing": ["bill", "pay", "charge", "invoice", "refund", "money", "card", "credit", "cost"],
            "technical": ["error", "broken", "bug", "issue", "problem", "crash", "fail", "glitch"],
            "sales": ["buy", "purchase", "pricing", "subscribe", "plan", "quote", "deal"],
            "order": ["order", "ship", "delivery", "track", "package", "item"],
            "account": ["account", "login", "password", "profile", "setting", "sign in"]
        }
        for intent, keywords in intent_loose_keywords.items():
            for kw in keywords:
                if kw in message_lower:
                    logger.info(f"Intent detected (loose): '{intent}' via keyword '{kw}'")
                    return intent, 0.6
        
        return None, 0.0
    
    async def run_with_fallback(
        self, 
        primary_fn, 
        fallback_fn = None,
        max_retries: int = 2
    ):
        """
        Execute a function with fallback and retry logic.
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await primary_fn()
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
        
        # Primary failed, try fallback
        if fallback_fn:
            logger.info("Using fallback function")
            try:
                return await fallback_fn()
            except Exception as e:
                logger.error(f"Fallback also failed: {e}")
        
        raise last_error

    async def reflect_and_correct(
        self,
        user_input: str,
        response: str,
        context: AgentContext,
        agent: Agent,
        llm_service: Any
    ) -> str:
        """
        Self-Correction / Reflection phase (Peak Agentic Feature).
        Reviews the response against success criteria and constraints.
        Also estimates LLM self-confidence and updates context.
        Uses the provided llm_service (caller should pass a fast/cheap model)
        to minimize latency impact.
        """
        # Skip if no criteria or simple response
        if not agent.success_criteria and not agent.failure_conditions:
            return response
            
        if len(response.split()) < 5:
            return response

        # Build Reflection Prompt with self-confidence rating
        criteria_str = "\n".join([f"- {c}" for c in (agent.success_criteria or [])])
        failures_str = "\n".join([f"- {f}" for f in (agent.failure_conditions or [])])
        
        reflection_prompt = f"""
        You are an AI Critic. Verify if the Assistant's response follows the goals and constraints.
        
        User Input: "{user_input}"
        Assistant Response: "{response}"
        
        SUCCESS CRITERIA:
        {criteria_str}
        
        FAILURE CONDITIONS (Avoid these):
        {failures_str}
        
        Evaluate the response:
        1. Is it appropriate? (yes/no)
        2. How confident are you that this is the correct response? (0.0-1.0)
        3. If it violates criteria, provide a CORRECTED version.
        
        Format your response exactly as:
        CONFIDENCE: <0.0-1.0>
        CORRECTED: <the corrected response or repeat verbatim>
        """
        
        logger.info(f"Reflection Phase active for agent: {agent.name}")
        corrected_response = await llm_service.generate_response(
            "Verify this response.", 
            reflection_prompt, 
            []
        )
        
        # Extract LLM self-confidence
        if corrected_response:
            for line in corrected_response.split("\n"):
                line = line.strip()
                if line.startswith("CONFIDENCE:"):
                    try:
                        conf_val = float(line.split(":")[1].strip())
                        context.confidence.llm_response = conf_val
                        context.confidence.update_overall()
                    except (ValueError, IndexError):
                        pass
                    break

        if corrected_response and corrected_response.strip() != response.strip():
            for line in corrected_response.split("\n"):
                if line.startswith("CORRECTED:"):
                    final_text = line.split(":", 1)[1].strip()
                    if final_text.lower() != "none" and len(final_text) > 2:
                        logger.info("Self-Correction Triggered: Response improved.")
                        return final_text
            
        return response


class ConversationState(str, Enum):
    """States in the conversation flow."""
    GREETING = "greeting"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    WAITING_FOR_TOOL = "waiting_for_tool"
    ESCALATING = "escalating"
    ENDED = "ended"


@dataclass
class ConversationFlow:
    """Manages conversation state machine."""
    session_id: str
    current_state: ConversationState = ConversationState.GREETING
    turn_count: int = 0
    max_turns: int = 50  # Prevent infinite loops
    
    def next_state(self, event: str) -> ConversationState:
        """Transition to next state based on event."""
        transitions = {
            (ConversationState.GREETING, "user_spoke"): ConversationState.PROCESSING,
            (ConversationState.LISTENING, "user_spoke"): ConversationState.PROCESSING,
            (ConversationState.PROCESSING, "response_ready"): ConversationState.RESPONDING,
            (ConversationState.PROCESSING, "tool_needed"): ConversationState.WAITING_FOR_TOOL,
            (ConversationState.WAITING_FOR_TOOL, "tool_complete"): ConversationState.PROCESSING,
            (ConversationState.RESPONDING, "response_sent"): ConversationState.LISTENING,
            (ConversationState.RESPONDING, "escalate"): ConversationState.ESCALATING,
            (ConversationState.ESCALATING, "transferred"): ConversationState.ENDED,
        }
        
        new_state = transitions.get((self.current_state, event), self.current_state)
        self.current_state = new_state
        self.turn_count += 1
        
        return new_state
    
    def can_continue(self) -> bool:
        """Check if conversation should continue."""
        return (
            self.current_state != ConversationState.ENDED and 
            self.turn_count < self.max_turns
        )
