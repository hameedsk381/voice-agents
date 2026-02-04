from deepgram import DeepgramClient
import os
import asyncio
from .base import STTProvider
from app.core.config import settings
from loguru import logger

class DeepgramSTT(STTProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.DEEPGRAM_API_KEY
        if not self.api_key:
            logger.warning("DEEPGRAM_API_KEY not found in settings.")
            self.client = None
        else:
            self.client = DeepgramClient(api_key=self.api_key)

    async def transcribe(self, audio_bytes: bytes, language: str = "en-US") -> str:
        """
        One-off transcription for an audio chunk.
        """
        if not self.client:
            return "Deepgram Key Missing"

        options = {
            "model": "nova-2",
            "smart_format": True,
        }
        
        if language == "auto":
            options["detect_language"] = True
        else:
            options["language"] = language
        
        response = self.client.listen.prerecorded.v("1").transcribe_file(
            {"buffer": audio_bytes, "mimetype": "audio/wav"}, 
            options
        )
        return response["results"]["channels"][0]["alternatives"][0]["transcript"]

    async def stream_connection(self):
        """
        Returns a live connection handler for WebSocket streaming.
        """
        if not self.client:
            return None
        
        dg_connection = self.client.listen.live.v("1")
        return dg_connection
