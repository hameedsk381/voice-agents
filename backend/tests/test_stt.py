import sys
import types

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.stt.types import TranscriptResult
from app.services.stt.mock_provider import MockSTT
from app.services.stt.factory import get_stt_provider, reset_stt_provider


def test_transcript_result_confidence_bounds():
    TranscriptResult(text="hi", confidence=0.5)
    with pytest.raises(ValueError):
        TranscriptResult(text="hi", confidence=1.5)


@pytest.mark.asyncio
async def test_mock_stt_returns_configurable_result():
    stt = MockSTT(default_text="order status please", default_confidence=0.42)
    result = await stt.transcribe(b"\x00\x01")
    assert result.text == "order status please"
    assert result.confidence == 0.42
    assert result.provider == "mock"


def test_stt_factory_mock_default():
    reset_stt_provider()
    with patch("app.services.stt.factory.settings") as mock_settings:
        mock_settings.STT_PROVIDER = "mock"
        provider = get_stt_provider()
        assert provider.__class__.__name__ == "MockSTT"


def test_stt_factory_deepgram():
    reset_stt_provider()
    fake_mod = types.ModuleType("app.services.stt.deepgram_provider")
    fake_instance = MagicMock(name="deepgram_stt")
    fake_mod.DeepgramSTT = MagicMock(return_value=fake_instance)
    sys.modules["app.services.stt.deepgram_provider"] = fake_mod
    try:
        with patch("app.services.stt.factory.settings") as mock_settings:
            mock_settings.STT_PROVIDER = "deepgram"
            provider = get_stt_provider()
            fake_mod.DeepgramSTT.assert_called_once()
            assert provider is fake_instance
    finally:
        sys.modules.pop("app.services.stt.deepgram_provider", None)
        reset_stt_provider()
