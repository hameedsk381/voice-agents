import os
import requests
import json
import asyncio
from typing import Optional
from .base import TTSProvider
from loguru import logger

class QwenTTS(TTSProvider):
    def __init__(self, base_url: str = "http://127.0.0.1:8008"):
        self.base_url = base_url

    async def synthesize(self, text: str, language: str = "en-US", voice: str = None, instruct: str = None) -> bytes:
        """
        Synthesize text using Qwen3-TTS v2.1.0.
        Uses multipart/form-data as per new documentation.
        """
        if not voice or voice == "auto":
            voice = "Vivian"

        url = f"{self.base_url}/tts/custom_voice"
        
        # multipart/form-data
        data = {
            "text": (None, text),
            "speaker": (None, voice),
            "language": (None, "Auto"),
            "instruct": (None, instruct or "")
        }

        try:
            # Run blocking request in thread
            # To send as multipart/form-data with no files, we pass a dict of {field: (None, value)} to files
            response = await asyncio.to_thread(requests.post, url, files=data)
        except Exception as e:
            logger.error(f"QwenTTS Connection Error: {e}")
            return b""

        if response.status_code == 200:
            return response.content
        else:
            logger.error(f"QwenTTS Error ({response.status_code}): {response.text}")
            return b""

    async def design_voice(self, text: str, instruct: str) -> bytes:
        """Create a unique voice from a description."""
        url = f"{self.base_url}/tts/voice_design"
        data = {
            "text": (None, text),
            "instruct": (None, instruct)
        }
        try:
            response = await asyncio.to_thread(requests.post, url, files=data)
            if response.status_code == 200:
                return response.content
            return b""
        except Exception as e:
            logger.error(f"Voice Design Error: {e}")
            return b""

    async def register_voice(self, name: str, ref_text: str, ref_audio_path: str) -> Optional[str]:
        """Clone a voice and register it."""
        url = f"{self.base_url}/voices"
        try:
            with open(ref_audio_path, "rb") as f:
                files = {
                    "name": (None, name),
                    "ref_text": (None, ref_text),
                    "ref_audio": (os.path.basename(ref_audio_path), f, "audio/wav")
                }
                response = await asyncio.to_thread(requests.post, url, files=files)
                if response.status_code == 200:
                    return response.json().get("id")
            return None
        except Exception as e:
            logger.error(f"Voice Registration Error: {e}")
            return None

    async def delete_voice(self, voice_id: str) -> bool:
        """Delete a registered voice."""
        url = f"{self.base_url}/voices/{voice_id}"
        try:
            response = await asyncio.to_thread(requests.delete, url)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Voice Deletion Error: {e}")
            return False

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
