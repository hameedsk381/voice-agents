from openai import AsyncOpenAI
import os
import asyncio
from typing import AsyncGenerator
from .base import LLMProvider
from app.core.config import settings

class OpenAILLM(LLMProvider):
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo", temperature: float = 0.7):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        self.temperature = temperature
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None

    async def generate_response(self, prompt: str, system_prompt: str, history: list) -> str:
        if not self.client:
            return f"Mock response to: {prompt}"

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": prompt}]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        return response.choices[0].message.content

    async def generate_stream(self, prompt: str, system_prompt: str, history: list) -> AsyncGenerator[str, None]:
        if not self.client:
            # Mock Stream
            mock_resp = f"This is a simulated AI response to '{prompt}' because no OpenAI Key was provided."
            for word in mock_resp.split(" "):
                yield word + " "
                await asyncio.sleep(0.1)
            return

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": prompt}]
        
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            temperature=self.temperature,
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
