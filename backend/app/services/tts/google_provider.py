from google.cloud import texttospeech

from app.core.config import settings
from app.services.tts.base import TTSProvider
from loguru import logger


class GoogleTTS(TTSProvider):
    def __init__(self) -> None:
        try:
            self.client = texttospeech.TextToSpeechAsyncClient()
        except Exception as e:
            logger.warning(f"Failed to create Google TTS client: {e}")
            self.client = None

    async def synthesize(self, text: str, language: str = "en-US", voice: str | None = None) -> bytes:
        if not self.client:
            return b""

        lang = language if language and language != "auto" else settings.GOOGLE_TTS_LANGUAGE
        voice_name = voice or settings.GOOGLE_TTS_VOICE

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice_selection = texttospeech.VoiceSelectionParams(
            language_code=lang,
            name=voice_name,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            speaking_rate=settings.GOOGLE_TTS_SPEAKING_RATE,
        )

        try:
            response = await self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice_selection,
                audio_config=audio_config,
            )
            return response.audio_content
        except Exception as e:
            logger.error(f"Google TTS error: {e}")
            return b""

    async def synthesize_stream(self, text_iterator, language: str = "en-US") -> bytes:
        async for chunk in text_iterator:
            audio = await self.synthesize(chunk, language=language)
            if audio:
                yield audio
