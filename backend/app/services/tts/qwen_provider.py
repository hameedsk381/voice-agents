import os
import requests
import json
import asyncio
from .base import TTSProvider
from loguru import logger

class QwenTTS(TTSProvider):
    def __init__(self, base_url: str = "http://127.0.0.1:8008"):
        self.base_url = base_url

    async def synthesize(self, text: str, language: str = "en-US", voice: str = None) -> bytes:
        """
        Synthesize text using Qwen3-TTS.
        Priority:
        1. If voice is a UUID, assume it's a saved voice -> /tts/voice_clone
        2. If voice is provided but not UUID, assume it's a standard speaker -> /tts/custom_voice
        3. Default to speaker "Vivian" -> /tts/custom_voice
        """
        if not voice or voice == "auto":
            voice = "Vivian"

        # Heuristic: Valid UUID means saved voice ID
        is_uuid = False
        try:
            if len(voice) == 36 and voice.count('-') == 4:
                is_uuid = True
        except:
            pass

        if is_uuid:
            # Use Voice Clone endpoint with saved voice_id
            url = f"{self.base_url}/tts/voice_clone"
            # Multipart form data needed for this endpoint based on OpenAPI docs?
            # Docs say: Body_voice_clone_tts_voice_clone_post: input is multipart/form-data
            # text (string), voice_id (string), language (string)
            
            # Using requests for multipart/form-data with no actual file (since we use voice_id)
            # We must send 'text', 'voice_id'. 
            data = {
                "text": text,
                "voice_id": voice,
                "language": "Auto" # Or map language if needed
            }
            try:
                # Run blocking request in thread
                response = await asyncio.to_thread(requests.post, url, data=data)
            except Exception as e:
                logger.error(f"QwenTTS Clone Connection Error: {e}")
                return b""

        else:
            # Use Custom Voice endpoint (Standard Speakers)
            url = f"{self.base_url}/tts/custom_voice"
            # Docs say: Body_custom_voice_tts_custom_voice_post: input is application/x-www-form-urlencoded
            # text, speaker, language
            data = {
                "text": text,
                "speaker": voice,
                "language": "Auto" 
            }
            try:
                # Run blocking request in thread
                response = await asyncio.to_thread(requests.post, url, data=data)
            except Exception as e:
                logger.error(f"QwenTTS Custom Connection Error: {e}")
                return b""

        if response.status_code == 200:
            return response.content
        else:
            logger.error(f"QwenTTS Error ({response.status_code}): {response.text}")
            return b""

    async def get_voices(self):
        """Fetch available voices from the service."""
        try:
            url = f"{self.base_url}/voices"
            response = await asyncio.to_thread(requests.get, url)
            if response.status_code == 200:
                saved_voices = response.json()
                # Format: [{id, name, ...}]
                params = []
                for v in saved_voices:
                    params.append({"id": v["id"], "name": f"{v['name']} (Cloned)", "type": "cloned"})
                
                # Add Standard Voices (Hardcoded based on typical Qwen/CosyVoice defaults or what we know)
                # If we don't know them, we can just add "Vivian" as default.
                standard = [
                    {"id": "Vivian", "name": "Vivian (Standard)", "type": "standard"},
                    {"id": "Long", "name": "Long (Standard e-book)", "type": "standard"},
                ]
                return standard + params
            return []
        except Exception as e:
            logger.error(f"Error fetching voices: {e}")
            return []

    async def synthesize_stream(self, text_iterator, language: str = "en-US", voice: str = None):
        """
        Synthesize text stream using Qwen3-TTS.
        Since Qwen3-TTS doesn't support streaming, we synthesize each chunk.
        """
        async for chunk in text_iterator:
            audio = await self.synthesize(chunk, language=language, voice=voice)
            if audio:
                yield audio
