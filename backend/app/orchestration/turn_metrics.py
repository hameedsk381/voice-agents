from dataclasses import dataclass, field, asdict
from typing import Dict, Any


@dataclass
class TurnMetrics:
    """Per-turn latency and decision telemetry (Phase 0 instrumentation)."""

    session_id: str
    turn_index: int
    path: str = "unknown"
    stt_ms: float = 0.0
    understand_ms: float = 0.0
    llm_ms: float = 0.0
    tool_ms: float = 0.0
    tts_ms: float = 0.0
    total_ms: float = 0.0
    confidence_vector: Dict[str, float] = field(default_factory=dict)
    policy_blocked: bool = False
    barge_in: bool = False
    stt_provider: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
