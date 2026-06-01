from typing import Optional

from app.core.config import settings
from app.services.tts.base import TTSProvider

_tts_instance: Optional[TTSProvider] = None


def get_tts_provider() -> TTSProvider:
    global _tts_instance
    if _tts_instance is None:
        provider = (settings.TTS_PROVIDER or "sarvam").lower()
        if provider == "deepgram":
            from app.services.tts.deepgram_provider import DeepgramTTS
            _tts_instance = DeepgramTTS()
        elif provider == "qwen":
            from app.services.tts.qwen_provider import QwenTTS
            _tts_instance = QwenTTS()
        elif provider == "google":
            from app.services.tts.google_provider import GoogleTTS
            _tts_instance = GoogleTTS()
        else:
            from app.services.tts.sarvam_provider import SarvamTTS
            _tts_instance = SarvamTTS()
    return _tts_instance


def reset_tts_provider() -> None:
    global _tts_instance
    _tts_instance = None
