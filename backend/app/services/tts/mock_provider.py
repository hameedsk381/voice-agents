from .base import TTSProvider
import asyncio

class MockTTS(TTSProvider):
    async def synthesize(self, text: str) -> bytes:
        # Return empty bytes for now, or load a static file if needed
        await asyncio.sleep(0.5)
        return b"mock_audio_data"

    async def synthesize_stream(self, text_iterator):
        async for text in text_iterator:
             yield b"mock_audio_chunk"
