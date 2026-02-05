from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

class Guardrail(BaseModel):
    name: str
    type: str # "regex", "semantic", "pii", "retry_limit"
    config: Dict[str, Any] = {}
    action: str = "block" # "block", "mask", "warn", "escalate"

class Transition(BaseModel):
    event: str
    target_state: str
    condition: Optional[str] = None # Optional script/expression to evaluate

class State(BaseModel):
    name: str
    enforce_script: Optional[str] = None
    allowed_intents: List[str] = []
    transitions: List[Transition] = []
    guardrails: List[Guardrail] = []
    mandatory_phrases: List[str] = []
    on_entry: List[str] = [] # Tool calls or notifications
    on_exit: List[str] = []
    is_sensitive: bool = False

class ConversationPolicy(BaseModel):
    version: str = "1.0"
    initial_state: str
    states: Dict[str, State]
    global_guardrails: List[Guardrail] = []
