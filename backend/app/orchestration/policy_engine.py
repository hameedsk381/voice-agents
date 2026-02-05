import re
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
from app.schemas.policy import ConversationPolicy, State, Guardrail, Transition

class PolicyEngine:
    """
    Enforces conversation policies and manages state transitions.
    The "Guardian" layer between the LLM and the real world.
    """
    
    def __init__(self, policy: ConversationPolicy):
        self.policy = policy
        
    def validate_input(self, current_state_name: str, user_input: str, detected_intent: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate user input against current state constraints.
        Returns (is_allowed, reason).
        """
        state = self.policy.states.get(current_state_name)
        if not state:
            return True, None # Default to allow if state not found? Or strict fail?
            
        # 1. Check intent constraints
        if state.allowed_intents and detected_intent:
            if detected_intent not in state.allowed_intents:
                logger.warning(f"Intent {detected_intent} not allowed in state {current_state_name}")
                return False, f"Intent {detected_intent} is not allowed in {current_state_name}"
        
        # 2. Check global and local guardrails
        for guardrail in self.policy.global_guardrails + state.guardrails:
            allowed, reason = self._check_guardrail(guardrail, user_input)
            if not allowed:
                return False, reason
                
        return True, None

    def validate_response(self, current_state_name: str, ai_response: str) -> Tuple[bool, str]:
        """
        Validate AI response against script enforcement and guardrails.
        Returns (is_valid, final_response).
        """
        state = self.policy.states.get(current_state_name)
        if not state:
            return True, ai_response

        # 1. Enforce Script if required
        if state.enforce_script:
            # Check for keyword overlap or similarity
            # In a production app, we would use an embedding model here.
            # For now, we'll do a loose keyword check + mandatory phrases.
            script_keywords = set(re.findall(r'\w+', state.enforce_script.lower()))
            response_keywords = set(re.findall(r'\w+', ai_response.lower()))
            overlap = len(script_keywords.intersection(response_keywords)) / max(len(script_keywords), 1)
            
            if overlap < 0.3:
                logger.warning(f"Script Adherence Failed (Overlap: {overlap:.2f}). Overriding with mandated script.")
                return True, state.enforce_script
            
            logger.info(f"Policy: Script Adherence Passed ({overlap:.2f})")

        # 2. Check Guardrails for PII, Disallowed phrases, etc.
        for guardrail in self.policy.global_guardrails + state.guardrails:
            allowed, reason = self._check_guardrail(guardrail, ai_response)
            if not allowed:
                logger.warning(f"Guardrail {guardrail.name} triggered: {reason}")
                if guardrail.action == "block":
                    return False, "I'm sorry, I cannot provide that information."
                elif guardrail.action == "escalate":
                    return False, "ESCALATE"

        # 3. Mandatory Phrasing (e.g. Legal Disclaimers)
        if state.mandatory_phrases:
            for phrase in state.mandatory_phrases:
                if phrase.lower() not in ai_response.lower():
                    logger.warning(f"Mandatory phrase missing in {current_state_name}: {phrase}")
                    return False, f"MISSING_MANDATORY: {phrase}"

        return True, ai_response

    def get_next_state(self, current_state_name: str, event: str) -> str:
        """Determines the next state based on transitions."""
        state = self.policy.states.get(current_state_name)
        if not state:
            return current_state_name
            
        for transition in state.transitions:
            if transition.event == event:
                logger.info(f"Transition: {current_state_name} -> {transition.target_state} on {event}")
                return transition.target_state
                
        return current_state_name

    def _check_guardrail(self, guardrail: Guardrail, text: str) -> Tuple[bool, Optional[str]]:
        """Internal helper to evaluate a specific guardrail."""
        if guardrail.type == "regex":
            pattern = guardrail.config.get("pattern")
            if pattern and re.search(pattern, text, re.IGNORECASE):
                return False, f"Matched disallowed pattern: {guardrail.name}"
        
        if guardrail.type == "pii":
            # Simple PII check (emails)
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            if re.search(email_pattern, text):
                return False, "PII detected (Email)"
                
        return True, None
