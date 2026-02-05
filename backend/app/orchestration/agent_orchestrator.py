"""
Multi-agent orchestration system.
Supports supervisor-worker patterns and dynamic agent routing.
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
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
    overall: float = 1.0


@dataclass
class AgentContext:
    """Context passed between agents."""
    session_id: str
    caller_id: Optional[str]
    history: List[Dict[str, str]]
    current_intent: Optional[str]
    extracted_info: Dict[str, Any]
    current_state: str = "initial"
    
    # New Elite Features
    confidence: ConfidenceScores = field(default_factory=ConfidenceScores)
    memory: List[MemoryItem] = None
    sentiment_slope: float = 1.0 # 0.0 (angry) to 1.0 (happy)
    
    escalation_needed: bool = False
    escalation_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.memory is None:
            self.memory = []


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
        """Analyze sentiment of user message (Simple Keyword based for now)."""
        text_lower = text.lower()
        positive_words = ["thank", "good", "great", "excellent", "happy", "yes", "correct", "perfect"]
        negative_words = ["bad", "angry", "frustrated", "wrong", "no", "stop", "terrible", "worst", "unhappy"]
        
        pos_score = sum(1 for w in positive_words if w in text_lower)
        neg_score = sum(1 for w in negative_words if w in text_lower)
        
        if pos_score > neg_score: return 1.0
        if neg_score > pos_score: return 0.0
        return 0.5 # Neutral

    def should_escalate(self, context: AgentContext, response: str, agent: Agent) -> tuple[bool, Optional[str]]:
        """
        Determine if the current context requires escalation.
        Returns (should_escalate, reason).
        """
        # 1. Check Agent-Specific Failure Conditions (Elite Feature)
        failure_conditions = agent.failure_conditions or []
        last_user_msg = context.history[-1]["content"].lower() if context.history else ""
        
        for condition in failure_conditions:
            # Simple keyword matching for now, can be expanded to LLM-based check
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
        
        # 4. Success Check (Exit if primary goal reached)
        success_criteria = agent.success_criteria or []
        for criteria in success_criteria:
            if criteria.lower() in response.lower():
                # Note: This might lead to "SUCCESS" instead of typical human escalation
                # For now, we follow the 'exit_actions' if defined
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
        """
        conf = context.confidence
        
        if conf.overall < 0.4:
            return "I'm sorry, I'm having trouble following our conversation. Let me transfer you to a human agent who can help."
            
        if conf.stt < 0.5:
            return "I apologize, but I didn't quite catch that over the line. Could you please repeat that more slowly?"
            
        if conf.intent < 0.5:
            return "I want to make sure I'm helping with the right thing. Could you clarify if you're asking about billing or technical support?"
            
        return None
    
    def detect_intent(self, user_message: str) -> Optional[str]:
        """Simple intent detection based on keywords."""
        message_lower = user_message.lower()
        
        intent_keywords = {
            "billing": ["bill", "payment", "charge", "invoice", "refund", "money"],
            "technical": ["error", "not working", "broken", "bug", "issue", "problem"],
            "sales": ["buy", "purchase", "pricing", "cost", "subscribe", "plan"],
            "order": ["order", "shipping", "delivery", "tracking", "package"],
            "account": ["account", "login", "password", "profile", "settings"],
        }
        
        for intent, keywords in intent_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return intent
        
        return None
    
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
        """
        # 1. Skip if no criteria or simple response
        if not agent.success_criteria and not agent.failure_conditions:
            return response
            
        if len(response.split()) < 5: # Too short to reflect on effectively
            return response

        # 2. Build Reflection Prompt
        criteria_str = "\n".join([f"- {c}" for c in (agent.success_criteria or [])])
        failures_str = "\n".join([f"- {f}" for f in (agent.failure_conditions or [])])
        
        reflection_prompt = f"""
        You are an AI Critic. Your job is to verify if the Assistant's response follows the goals and constraints.
        
        User Input: "{user_input}"
        Assistant Response: "{response}"
        
        SUCCESS CRITERIA:
        {criteria_str}
        
        FAILURE CONDITIONS (Avoid these):
        {failures_str}
        
        Is the response appropriate? If it violates any criteria or failure conditions, provide a CORRECTED version.
        If it is good, just repeat the original response.
        
        Return ONLY the final response text.
        """
        
        logger.info(f"Reflection Phase active for agent: {agent.name}")
        corrected_response = await llm_service.generate_response(
            "Verify this response.", 
            reflection_prompt, 
            [] # No history for reflection to keep it focused
        )
        
        if corrected_response and corrected_response.strip() != response.strip():
            # Check for a "Corrected: " prefix or similar if LLM is chatty, but we asked for ONLY text
            final_text = corrected_response.strip()
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
