from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
from .groq_provider import GroqLLM
from .health_manager import health_manager
import time
from loguru import logger

class EnterpriseLLM:
    """
    A multi-provider, latency-aware, health-tracking LLM service.
    """
    def __init__(self, primary_model: str = "llama-3.3-70b-versatile"):
        self.primary_provider = GroqLLM(model=primary_model)
        # In a real enterprise app, we'd have Anthropic or OpenAI here too
        self.fallback_provider = GroqLLM(model="llama-3.1-8b-instant")
        
    async def generate_response(self, prompt: str, system_prompt: str, history: list, tools: list = None) -> str:
        start_time = time.time()
        try:
            # Check Health
            if health_manager.get_health_score("groq") < 0.5:
                 logger.warning("Primary provider health low, attempting to use fallback/degraded mode.")
                 # In prod, this would switch to a different API key or cloud provider

            response = await self.primary_provider.generate_response(prompt, system_prompt, history, tools)
            latency = (time.time() - start_time) * 1000
            health_manager.record_success("groq", latency)
            return response
        except Exception as e:
            health_manager.record_failure("groq")
            logger.error(f"Primary Provider Failed: {e}. Switching to Failover.")
            return await self.fallback_provider.generate_response(prompt, system_prompt, history, tools)

    async def generate_stream(self, prompt: str, system_prompt: str, history: list) -> AsyncGenerator[str, None]:
        # Simple streaming passthrough
        async for chunk in self.primary_provider.generate_stream(prompt, system_prompt, history):
            yield chunk

    async def generate_with_tools(
        self, 
        prompt: str, 
        system_prompt: str, 
        history: list,
        tools: list = None
    ) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
        start_time = time.time()
        try:
            res, tools_calls = await self.primary_provider.generate_with_tools(prompt, system_prompt, history, tools)
            health_manager.record_success("groq", (time.time() - start_time) * 1000)
            return res, tools_calls
        except Exception as e:
            health_manager.record_failure("groq")
            return await self.fallback_provider.generate_with_tools(prompt, system_prompt, history, tools)

    @property
    def model(self):
        return self.primary_provider.model
    
    @model.setter
    def model(self, value):
        self.primary_provider.model = value
