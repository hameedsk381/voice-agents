from .base import STTProvider
import asyncio

class MockSTT(STTProvider):
    async def transcribe(self, audio_bytes: bytes) -> str:
        # Mock transcription for testing without API usage
        await asyncio.sleep(0.5) 
        return "This is a simulated transcription of the user's voice."
