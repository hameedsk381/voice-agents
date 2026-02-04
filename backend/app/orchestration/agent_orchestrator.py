"""
Multi-agent orchestration system.
Supports supervisor-worker patterns and dynamic agent routing.
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from loguru import logger
from app.models.agent import Agent
from sqlalchemy.orm import Session


class AgentRole(str, Enum):
    """Types of agent roles in orchestration."""
    PRIMARY = "primary"         # Main agent handling the call
    SUPERVISOR = "supervisor"   # Oversees other agents
    SPECIALIST = "specialist"   # Handles specific domain
    VALIDATOR = "validator"     # Validates responses
    FALLBACK = "fallback"       # Backup agent


@dataclass
class AgentContext:
    """Context passed between agents."""
    session_id: str
    caller_id: Optional[str]
    history: List[Dict[str, str]]
    current_intent: Optional[str]
    extracted_info: Dict[str, Any]
    escalation_needed: bool = False
    escalation_reason: Optional[str] = None


class AgentOrchestrator:
    """
    Orchestrates multiple agents in a conversation.
    Handles routing, fallback, and escalation logic.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.agent_cache: Dict[str, Agent] = {}
    
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
    
    def should_escalate(self, context: AgentContext, response: str) -> tuple[bool, Optional[str]]:
        """
        Determine if the current context requires escalation.
        Returns (should_escalate, reason).
        """
        # Check for explicit escalation triggers in response
        escalation_keywords = [
            "speak to a human",
            "transfer to agent",
            "manager",
            "supervisor",
            "not satisfied",
            "complaint"
        ]
        
        last_user_msg = context.history[-1]["content"].lower() if context.history else ""
        
        for keyword in escalation_keywords:
            if keyword in last_user_msg:
                return True, f"User requested: {keyword}"
        
        # Check for repeated questions (frustration signal)
        if len(context.history) > 6:
            recent_user_msgs = [h["content"] for h in context.history[-6:] if h["role"] == "user"]
            if len(set(recent_user_msgs)) < len(recent_user_msgs) / 2:
                return True, "User repeating questions (possible frustration)"
        
        return False, None
    
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
