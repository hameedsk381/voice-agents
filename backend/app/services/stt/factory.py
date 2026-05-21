from typing import Optional

from app.core.config import settings
from app.services.stt.base import STTProvider
from app.services.stt.mock_provider import MockSTT

_stt_instance: Optional[STTProvider] = None


def get_stt_provider() -> STTProvider:
    """Return the configured STT provider singleton."""
    global _stt_instance
    if _stt_instance is None:
        provider = (settings.STT_PROVIDER or "mock").lower()
        if provider == "deepgram":
            from app.services.stt.deepgram_provider import DeepgramSTT
            _stt_instance = DeepgramSTT()
        else:
            _stt_instance = MockSTT()
    return _stt_instance


def reset_stt_provider() -> None:
    """Clear cached provider (tests)."""
    global _stt_instance
    _stt_instance = None
