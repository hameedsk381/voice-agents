from google.cloud import speech

from app.core.config import settings
from app.services.stt.base import STTProvider
from app.services.stt.types import TranscriptResult
from loguru import logger


class GoogleSTT(STTProvider):
    def __init__(self) -> None:
        try:
            self.client = speech.SpeechAsyncClient()
        except Exception as e:
            logger.warning(f"Failed to create Google STT client: {e}")
            self.client = None

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "en-US",
        mimetype: str = "audio/wav",
    ) -> TranscriptResult:
        if not self.client:
            return TranscriptResult(
                text="Google STT client not available",
                confidence=0.0,
                is_final=True,
                provider="google",
            )

        encoding_map = {
            "audio/wav": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            "audio/webm": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            "audio/ogg": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
            "audio/flac": speech.RecognitionConfig.AudioEncoding.FLAC,
        }
        encoding = encoding_map.get(mimetype, speech.RecognitionConfig.AudioEncoding.LINEAR16)
        lang = language if language and language != "auto" else settings.GOOGLE_STT_LANGUAGE

        config = speech.RecognitionConfig(
            encoding=encoding,
            language_code=lang,
            model="latest_long",
            enable_automatic_punctuation=True,
        )
        audio = speech.RecognitionAudio(content=audio_bytes)

        try:
            response = await self.client.recognize(config=config, audio=audio)
            if not response.results:
                return TranscriptResult(text="", confidence=0.0, is_final=True, provider="google")

            best = response.results[0]
            alt = best.alternatives[0]
            return TranscriptResult(
                text=alt.transcript or "",
                confidence=alt.confidence if alt.confidence else settings.DEFAULT_STT_CONFIDENCE,
                is_final=True,
                provider="google",
            )
        except Exception as e:
            logger.error(f"Google STT error: {e}")
            return TranscriptResult(text="", confidence=0.0, is_final=True, provider="google")
