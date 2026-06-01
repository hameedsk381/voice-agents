import base64
from typing import Optional, List
import httpx
from loguru import logger

from app.core.config import settings
from app.services.tts.base import TTSProvider


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
}

_VOICES: list[dict] = [
    {"id": "shubh", "name": "Shubh", "type": "standard"},
    {"id": "aditya", "name": "Aditya", "type": "standard"},
    {"id": "ritu", "name": "Ritu", "type": "standard"},
    {"id": "priya", "name": "Priya", "type": "standard"},
    {"id": "neha", "name": "Neha", "type": "standard"},
    {"id": "rahul", "name": "Rahul", "type": "standard"},
    {"id": "pooja", "name": "Pooja", "type": "standard"},
    {"id": "rohan", "name": "Rohan", "type": "standard"},
    {"id": "simran", "name": "Simran", "type": "standard"},
    {"id": "kavya", "name": "Kavya", "type": "standard"},
    {"id": "amit", "name": "Amit", "type": "standard"},
    {"id": "dev", "name": "Dev", "type": "standard"},
    {"id": "ishita", "name": "Ishita", "type": "standard"},
    {"id": "shreya", "name": "Shreya", "type": "standard"},
    {"id": "ratan", "name": "Ratan", "type": "standard"},
    {"id": "varun", "name": "Varun", "type": "standard"},
    {"id": "manan", "name": "Manan", "type": "standard"},
    {"id": "sumit", "name": "Sumit", "type": "standard"},
    {"id": "roopa", "name": "Roopa", "type": "standard"},
    {"id": "kabir", "name": "Kabir", "type": "standard"},
    {"id": "aayan", "name": "Aayan", "type": "standard"},
    {"id": "ashutosh", "name": "Ashutosh", "type": "standard"},
    {"id": "advait", "name": "Advait", "type": "standard"},
    {"id": "anand", "name": "Anand", "type": "standard"},
    {"id": "tanya", "name": "Tanya", "type": "standard"},
    {"id": "tarun", "name": "Tarun", "type": "standard"},
    {"id": "sunny", "name": "Sunny", "type": "standard"},
    {"id": "mani", "name": "Mani", "type": "standard"},
    {"id": "gokul", "name": "Gokul", "type": "standard"},
    {"id": "vijay", "name": "Vijay", "type": "standard"},
    {"id": "shruti", "name": "Shruti", "type": "standard"},
    {"id": "suhani", "name": "Suhani", "type": "standard"},
    {"id": "mohit", "name": "Mohit", "type": "standard"},
    {"id": "kavitha", "name": "Kavitha", "type": "standard"},
    {"id": "rehan", "name": "Rehan", "type": "standard"},
    {"id": "soham", "name": "Soham", "type": "standard"},
    {"id": "rupali", "name": "Rupali", "type": "standard"},
    {"id": "anushka", "name": "Anushka (v2)", "type": "standard"},
    {"id": "abhilash", "name": "Abhilash (v2)", "type": "standard"},
    {"id": "manisha", "name": "Manisha (v2)", "type": "standard"},
    {"id": "vidya", "name": "Vidya (v2)", "type": "standard"},
    {"id": "arya", "name": "Arya (v2)", "type": "standard"},
    {"id": "karun", "name": "Karun (v2)", "type": "standard"},
    {"id": "hitesh", "name": "Hitesh (v2)", "type": "standard"},
]


class SarvamTTS(TTSProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SARVAM_API_KEY
        self.base_url = "https://api.sarvam.ai"
        self.default_voice = "shubh"

    def _map_language(self, language: str) -> str:
        return _LANG_TO_SARVAM.get(language, "en-IN")

    async def synthesize(
        self,
        text: str,
        language: str = "en-US",
        voice: Optional[str] = None,
        pace: Optional[float] = None,
    ) -> bytes:
        if not self.api_key or not text:
            return b""

        lang_code = self._map_language(language)
        speaker = voice if voice and voice != "auto" else self.default_voice

        payload = {
            "text": text,
            "target_language_code": lang_code,
            "speaker": speaker,
            "model": "bulbul:v3",
            "output_audio_codec": "wav",
            "speech_sample_rate": "24000",
        }
        if pace is not None:
            payload["pace"] = max(0.5, min(2.0, pace))

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/text-to-speech",
                    headers={
                        "api-subscription-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

            audios = data.get("audios", [])
            if not audios:
                logger.warning("Sarvam TTS returned empty audios array")
                return b""

            return base64.b64decode(audios[0])
        except httpx.TimeoutException:
            logger.error("Sarvam TTS request timed out")
            return b""
        except Exception as e:
            logger.error(f"Sarvam TTS error: {e}")
            return b""

    async def synthesize_stream(self, text_iterator, language: str = "en-US", voice: Optional[str] = None):
        async for chunk in text_iterator:
            audio = await self.synthesize(chunk, language=language, voice=voice)
            if audio:
                yield audio

    async def get_voices(self) -> list[dict]:
        return _VOICES
