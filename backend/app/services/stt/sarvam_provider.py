import io
from typing import Optional
import httpx
from loguru import logger

from app.core.config import settings
from app.services.stt.base import STTProvider
from app.services.stt.types import TranscriptResult


_LANG_TO_SARVAM: dict[str, str] = {
    "hi": "hi-IN",
    "hi-IN": "hi-IN",
    "bn": "bn-IN",
    "bn-IN": "bn-IN",
    "kn": "kn-IN",
    "kn-IN": "kn-IN",
    "ml": "ml-IN",
    "ml-IN": "ml-IN",
    "mr": "mr-IN",
    "mr-IN": "mr-IN",
    "or": "od-IN",
    "or-IN": "od-IN",
    "pa": "pa-IN",
    "pa-IN": "pa-IN",
    "ta": "ta-IN",
    "ta-IN": "ta-IN",
    "te": "te-IN",
    "te-IN": "te-IN",
    "gu": "gu-IN",
    "gu-IN": "gu-IN",
    "en": "en-IN",
    "en-US": "en-IN",
    "en-IN": "en-IN",
    "as": "as-IN",
    "as-IN": "as-IN",
    "ur": "ur-IN",
    "ur-IN": "ur-IN",
}

_MIMETYPE_TO_CODEC: dict[str, str] = {
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/ogg": "ogg",
    "audio/opus": "opus",
    "audio/flac": "flac",
    "audio/webm": "webm",
    "audio/mp4": "mp4",
    "audio/x-m4a": "mp4",
    "audio/aac": "aac",
    "audio/amr": "amr",
}


class SarvamSTT(STTProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SARVAM_API_KEY
        self.base_url = "https://api.sarvam.ai"

    def _map_language(self, language: str) -> str:
        return _LANG_TO_SARVAM.get(language, "en-IN")

    def _mimetype_to_codec(self, mimetype: str) -> str:
        base = mimetype.split(";")[0].strip().lower()
        return _MIMETYPE_TO_CODEC.get(base, "wav")

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "en-US",
        mimetype: str = "audio/wav",
    ) -> TranscriptResult:
        if not self.api_key:
            logger.warning("SARVAM_API_KEY not configured")
            return TranscriptResult(
                text="",
                confidence=0.0,
                is_final=True,
                provider="sarvam",
            )

        lang_code = self._map_language(language)
        codec = self._mimetype_to_codec(mimetype)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/speech-to-text",
                    headers={"api-subscription-key": self.api_key},
                    files={
                        "file": ("audio", audio_bytes, mimetype),
                    },
                    data={
                        "model": "saaras:v3",
                        "mode": "transcribe",
                        "language_code": lang_code,
                        "input_audio_codec": codec,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            transcript = data.get("transcript", "")
            language_probability = data.get("language_probability")

            confidence = language_probability if language_probability is not None else settings.DEFAULT_STT_CONFIDENCE

            return TranscriptResult(
                text=transcript,
                confidence=min(max(confidence, 0.0), 1.0),
                is_final=True,
                provider="sarvam",
            )
        except httpx.TimeoutException:
            logger.error("Sarvam STT request timed out")
            return TranscriptResult(text="", confidence=0.0, is_final=True, provider="sarvam")
        except Exception as e:
            logger.error(f"Sarvam STT error: {e}")
            return TranscriptResult(text="", confidence=0.0, is_final=True, provider="sarvam")
