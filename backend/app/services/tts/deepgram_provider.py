import os
import requests
from .base import TTSProvider
from app.core.config import settings
from loguru import logger

class DeepgramTTS(TTSProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.DEEPGRAM_API_KEY

    async def synthesize(self, text: str, language: str = "en-US") -> bytes:
        if not self.api_key:
            return b"mock_audio_missing_key"

        # Map language to models
        lang_main = language.split("-")[0].lower()
        model_map = {
            "en": "aura-asteria-en",
            "es": "aura-luna-es",
            "fr": "aura-luna-fr",
            "de": "aura-luna-de",
            "pt": "aura-luna-pt",
        }
        
        selected_model = model_map.get(lang_main, "aura-asteria-en")
        url = f"https://api.deepgram.com/v1/speak?model={selected_model}"

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {"text": text}

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Deepgram TTS Error: {response.status_code} - {response.text}")
                return b""
        except Exception as e:
            logger.error(f"TTS Exception: {e}")
            return b""

    async def synthesize_stream(self, text_iterator, language: str = "en-US"):
        async for chunk in text_iterator:
            audio = await self.synthesize(chunk, language=language)
            if audio:
                yield audio
