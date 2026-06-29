"""
Anthropic Claude provider for high-stakes reasoning (compliance audit,
outcome classification). Implements the shared LLMProvider interface.

Gracefully degrades to a clear mock response when the SDK is not installed
or no API key is configured (mirrors the other providers).
"""

import asyncio
from typing import AsyncGenerator, List

from loguru import logger

from .base import LLMProvider
from app.core.config import settings


class AnthropicLLM(LLMProvider):
    def __init__(
        self,
        api_key: str = None,
        model: str = "claude-sonnet-4-6",
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = None
        if self.api_key:
            try:
                from anthropic import AsyncAnthropic
                self.client = AsyncAnthropic(api_key=self.api_key)
            except Exception as exc:  # SDK missing or init error
                logger.warning(f"Anthropic SDK unavailable, using mock: {exc}")
                self.client = None

    @staticmethod
    def _to_messages(history: list, prompt: str) -> List[dict]:
        # Anthropic takes system separately; messages must be user/assistant only.
        messages = []
        for turn in history or []:
            role = turn.get("role")
            if role in ("user", "assistant") and turn.get("content"):
                messages.append({"role": role, "content": str(turn["content"])})
        messages.append({"role": "user", "content": prompt})
        return messages

    async def generate_response(self, prompt: str, system_prompt: str, history: list) -> str:
        if not self.client:
            raise RuntimeError("Anthropic LLM not configured: set ANTHROPIC_API_KEY (and install the anthropic SDK)")
        try:
            resp = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt or "",
                messages=self._to_messages(history, prompt),
            )
            parts = [block.text for block in resp.content if getattr(block, "type", None) == "text"]
            return "".join(parts).strip()
        except Exception as exc:
            logger.error(f"Anthropic generate_response failed ({self.model}): {exc}")
            raise

    async def generate_stream(self, prompt: str, system_prompt: str, history: list) -> AsyncGenerator[str, None]:
        if not self.client:
            raise RuntimeError("Anthropic LLM not configured: set ANTHROPIC_API_KEY (and install the anthropic SDK)")
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt or "",
            messages=self._to_messages(history, prompt),
        ) as stream:
            async for text in stream.text_stream:
                yield text
