import os
import pytest

from app.core.config import settings
from app.services.stt.deepgram_provider import DeepgramSTT


@pytest.mark.integration
@pytest.mark.asyncio
async def test_deepgram_transcribe_fixture():
    if not settings.DEEPGRAM_API_KEY or settings.DEEPGRAM_API_KEY.startswith("your-"):
        pytest.skip("DEEPGRAM_API_KEY not configured")

    # Minimal valid WAV header + silence (Deepgram accepts short clips)
    wav_header = (
        b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
        b"\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    )
    stt = DeepgramSTT()
    result = await stt.transcribe(wav_header, language="en-US", mimetype="audio/wav")
    assert isinstance(result.text, str)
    assert 0.0 <= result.confidence <= 1.0
    assert result.provider == "deepgram"
