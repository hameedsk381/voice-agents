import asyncio
import os
from typing import Optional

from app.core.config import settings
from app.services.stt.base import STTProvider
from app.services.stt.types import TranscriptResult


class MockSTT(STTProvider):
    """Configurable mock STT for local dev and tests."""

    def __init__(
        self,
        default_text: Optional[str] = None,
        default_confidence: Optional[float] = None,
    ):
        self.default_text = (
            default_text
            or os.getenv("MOCK_STT_TEXT")
            or "This is a simulated transcription of the user's voice."
        )
        self.default_confidence = (
            default_confidence
            if default_confidence is not None
            else float(os.getenv("MOCK_STT_CONFIDENCE", str(settings.DEFAULT_STT_CONFIDENCE)))
        )

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "en-US",
        mimetype: str = "audio/wav",
    ) -> TranscriptResult:
        await asyncio.sleep(0.05)
        return TranscriptResult(
            text=self.default_text,
            confidence=self.default_confidence,
            is_final=True,
            provider="mock",
        )
