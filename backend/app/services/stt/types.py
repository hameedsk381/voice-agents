from dataclasses import dataclass


@dataclass(frozen=True)
class TranscriptResult:
    """STT output with confidence for downstream decisioning."""

    text: str
    confidence: float
    is_final: bool = True
    provider: str = "unknown"

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")
