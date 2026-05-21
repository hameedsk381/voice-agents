from deepgram import DeepgramClient

from app.core.config import settings
from app.services.stt.base import STTProvider
from app.services.stt.types import TranscriptResult
from loguru import logger


class DeepgramSTT(STTProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.DEEPGRAM_API_KEY
        if not self.api_key:
            logger.warning("DEEPGRAM_API_KEY not found in settings.")
            self.client = None
        else:
            self.client = DeepgramClient(api_key=self.api_key)

    def _extract_confidence(self, response: dict) -> float:
        try:
            alt = response["results"]["channels"][0]["alternatives"][0]
            if "confidence" in alt and alt["confidence"] is not None:
                return float(alt["confidence"])
            words = alt.get("words") or []
            if words:
                confidences = [w.get("confidence") for w in words if w.get("confidence") is not None]
                if confidences:
                    return sum(confidences) / len(confidences)
        except (KeyError, IndexError, TypeError, ValueError) as e:
            logger.debug(f"Could not parse Deepgram confidence: {e}")
        return settings.DEFAULT_STT_CONFIDENCE

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "en-US",
        mimetype: str = "audio/wav",
    ) -> TranscriptResult:
        if not self.client:
            return TranscriptResult(
                text="Deepgram API key missing",
                confidence=0.0,
                is_final=True,
                provider="deepgram",
            )

        options = {
            "model": "nova-2",
            "smart_format": True,
        }

        if language == "auto":
            options["detect_language"] = True
        else:
            options["language"] = language

        response = self.client.listen.prerecorded.v("1").transcribe_file(
            {"buffer": audio_bytes, "mimetype": mimetype},
            options,
        )
        transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]
        confidence = self._extract_confidence(response)
        return TranscriptResult(
            text=transcript or "",
            confidence=confidence,
            is_final=True,
            provider="deepgram",
        )

    async def stream_connection(self):
        """Returns a live connection handler for WebSocket streaming."""
        if not self.client:
            return None

        dg_connection = self.client.listen.live.v("1")
        return dg_connection
