import base64
import asyncio
from typing import Dict, List, Optional
from loguru import logger

class VoiceUXService:
    """
    Manages high-fidelity Voice UX elements:
    - Micro-acknowledgements (Backchanneling)
    - Latency Fillers
    - Adaptive pacing markers
    """
    
    def __init__(self, tts_service):
        self.tts = tts_service
        self.backchannel_cache: Dict[str, str] = {} # token -> base64 audio
        self.filler_cache: Dict[str, str] = {}
        
        # Pre-defined tokens for premium feel
        self.backchannel_tokens = ["mm-hm", "I see", "Right", "Okay", "Got it"]
        self.latency_fillers = [
            "Let me check that for you...",
            "One moment while I pull that up...",
            "Let me see...",
            "Checking my records..."
        ]

    async def precompute_tokens(self, voice: str = "Vivian"):
        """Warm up the cache with standard UX tokens."""
        logger.info(f"Precomputing Voice UX tokens for voice: {voice}")
        
        tasks = []
        for token in self.backchannel_tokens + self.latency_fillers:
            tasks.append(self._cache_token(token, voice))
        
        await asyncio.gather(*tasks)

    async def _cache_token(self, text: str, voice: str):
        # Apply voice instructions if supported
        instruct = None
        if text in self.backchannel_tokens:
            instruct = "quick, soft, attentive"
        else:
            instruct = "slow, thoughtful, professional"

        # Check if synthesize supports instruct
        import inspect
        sig = inspect.signature(self.tts.synthesize)
        
        if 'instruct' in sig.parameters:
            audio_bytes = await self.tts.synthesize(text, voice=voice, instruct=instruct)
        else:
            audio_bytes = await self.tts.synthesize(text, voice=voice)
            
        if audio_bytes:
            b64 = base64.b64encode(audio_bytes).decode('utf-8')
            if text in self.backchannel_tokens:
                self.backchannel_cache[text] = b64
            else:
                self.filler_cache[text] = b64

    def get_random_backchannel(self) -> Optional[str]:
        import random
        token = random.choice(self.backchannel_tokens)
        return self.backchannel_cache.get(token)

    def get_random_filler(self) -> Optional[str]:
        import random
        token = random.choice(self.latency_fillers)
        return self.filler_cache.get(token)

    async def send_backchannel(self, websocket, token: str = None):
        """Send a quick micro-acknowledgement."""
        import random
        if not token:
            token = random.choice(self.backchannel_tokens)
        
        audio_b64 = self.backchannel_cache.get(token)
        if audio_b64:
            await websocket.send_json({
                "type": "audio", 
                "data": audio_b64, 
                "metadata": {"ux_type": "backchannel", "text": token}
            })

    async def send_filler(self, websocket):
        """Send a latency filler to buy time."""
        import random
        token = random.choice(self.latency_fillers)
        audio_b64 = self.filler_cache.get(token)
        if audio_b64:
            await websocket.send_json({
                "type": "audio", 
                "data": audio_b64, 
                "metadata": {"ux_type": "filler", "text": token}
            })
