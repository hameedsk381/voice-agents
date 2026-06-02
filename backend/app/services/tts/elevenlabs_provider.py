import os
import requests
import json
import asyncio
from typing import Optional, List, Dict, Any
from .base import TTSProvider
from app.core.config import settings
from loguru import logger

class ElevenLabsTTS(TTSProvider):
    def __init__(self):
        # Fallback API key for testing if not set
        self.api_key = getattr(settings, "ELEVENLABS_API_KEY", os.getenv("ELEVENLABS_API_KEY", ""))
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def synthesize(self, text: str, language: str = "en-US", voice: str = None, instruct: str = None) -> bytes:
        """Synthesize text using ElevenLabs API."""
        if not voice or voice == "auto":
            voice = "21m00Tcm4TlvDq8ikWAM" # Rachel default
            
        url = f"{self.base_url}/text-to-speech/{voice}"
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        try:
            response = await asyncio.to_thread(requests.post, url, json=data, headers=self.headers)
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"ElevenLabs TTS Error ({response.status_code}): {response.text}")
                return b""
        except Exception as e:
            logger.error(f"ElevenLabs Connection Error: {e}")
            return b""

    async def synthesize_stream(self, text_iterator, language: str = "en-US", voice: str = None):
        """Consume text stream and yield audio bytes."""
        async for chunk in text_iterator:
            audio = await self.synthesize(chunk, language=language, voice=voice)
            if audio:
                yield audio

    async def get_voices(self) -> List[Dict[str, Any]]:
        """Fetch available voices from ElevenLabs."""
        url = f"{self.base_url}/voices"
        try:
            response = await asyncio.to_thread(requests.get, url, headers=self.headers)
            if response.status_code == 200:
                voices_data = response.json().get("voices", [])
                
                formatted_voices = []
                for v in voices_data:
                    # Mark cloned vs standard based on ElevenLabs category
                    category = v.get("category", "standard")
                    is_cloned = category in ["cloned", "generated", "professional"]
                    
                    formatted_voices.append({
                        "id": v["voice_id"],
                        "name": f"{v['name']} ({category.capitalize()})",
                        "type": "cloned" if is_cloned else "standard",
                        "primaryLanguage": "en" # Default for now
                    })
                return formatted_voices
            return []
        except Exception as e:
            logger.error(f"Error fetching ElevenLabs voices: {e}")
            return []

    async def design_voice(self, text: str, instruct: str) -> bytes:
        """
        Preview a designed voice.
        ElevenLabs voice design typically requires specific parameters (gender, age, accent).
        Since we only have an 'instruct' string, we'll synthesize using a default standard voice as a placeholder
        for the dashboard preview until a structured form is implemented.
        """
        # Fallback to standard synthesis for the preview
        logger.info(f"ElevenLabs voice design preview requested with prompt: {instruct}")
        return await self.synthesize(text, voice="21m00Tcm4TlvDq8ikWAM")

    async def register_voice(self, name: str, ref_text: str, ref_audio_path: str) -> Optional[str]:
        """Clone a voice and register it in ElevenLabs."""
        url = f"{self.base_url}/voices/add"
        
        headers = {
            "xi-api-key": self.api_key,
            # Don't set Content-Type here, let requests handle multipart boundary
        }
        
        try:
            with open(ref_audio_path, "rb") as f:
                files = {
                    "files": (os.path.basename(ref_audio_path), f, "audio/wav")
                }
                data = {
                    "name": name,
                    "description": ref_text
                }
                response = await asyncio.to_thread(requests.post, url, files=files, data=data, headers=headers)
                if response.status_code == 200:
                    return response.json().get("voice_id")
                else:
                    logger.error(f"ElevenLabs Clone Error: {response.text}")
                    return None
        except Exception as e:
            logger.error(f"ElevenLabs Voice Registration Error: {e}")
            return None

    async def delete_voice(self, voice_id: str) -> bool:
        """Delete a registered voice."""
        url = f"{self.base_url}/voices/{voice_id}"
        try:
            response = await asyncio.to_thread(requests.delete, url, headers=self.headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"ElevenLabs Voice Deletion Error: {e}")
            return False
