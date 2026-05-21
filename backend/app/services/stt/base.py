from abc import ABC, abstractmethod
from typing import Optional

from app.services.stt.types import TranscriptResult


class STTProvider(ABC):
    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "en-US",
        mimetype: str = "audio/wav",
    ) -> TranscriptResult:
        """Transcribe audio bytes to text with confidence."""

    async def transcribe_text(self, text: str) -> TranscriptResult:
        """Backward-compatible helper when audio is already text (tests / passthrough)."""
        return TranscriptResult(text=text, confidence=1.0, is_final=True, provider="passthrough")
