import os
import asyncio
import json
import time
from typing import AsyncGenerator, Optional, Tuple, List, Dict, Any
from groq import AsyncGroq
from .base import LLMProvider
from app.core.config import settings
from app.core.telemetry import get_tracer, persist_span

_tracer = get_tracer("groq_llm")

class GroqLLM(LLMProvider):
    def __init__(self, api_key: str = None, model: str = "llama-3.3-70b-versatile", temperature: float = 0.7):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model
        self.temperature = temperature
        if self.api_key:
            self.client = AsyncGroq(api_key=self.api_key)
        else:
            self.client = None

    async def generate_response(self, prompt: str, system_prompt: str, history: list, tools: list = None) -> str:
        t0 = time.perf_counter()
        status = "OK"
        msg = ""
        try:
            if not self.client:
                raise RuntimeError("Groq LLM not configured: set GROQ_API_KEY")

            messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": prompt}]

            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            status = "ERROR"
            msg = str(e)
            raise
        finally:
            persist_span(None, "groq.generate_response", "llm",
                (time.perf_counter() - t0) * 1000,
                {"model": self.model, "prompt_length": len(prompt)},
                status_code=status, status_message=msg)

    async def generate_with_tools(
        self, 
        prompt: str, 
        system_prompt: str, 
        history: list,
        tools: list = None
    ) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
        t0 = time.perf_counter()
        try:
            if not self.client:
                raise RuntimeError("Groq LLM not configured: set GROQ_API_KEY")

            messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            
            response = await self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message
            
            tool_calls = None
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_calls = []
                for tc in message.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments)
                    })
            
            return message.content, tool_calls
        except Exception as e:
            persist_span(None, "groq.generate_with_tools", "llm",
                (time.perf_counter() - t0) * 1000,
                {"model": self.model, "has_tools": bool(tools)},
                status_code="ERROR", status_message=str(e))
            raise
        finally:
            persist_span(None, "groq.generate_with_tools", "llm",
                (time.perf_counter() - t0) * 1000,
                {"model": self.model, "has_tools": bool(tools)})

    async def generate_stream(self, prompt: str, system_prompt: str, history: list) -> AsyncGenerator[str, None]:
        t0 = time.perf_counter()
        tokens = 0
        try:
            if not self.client:
                raise RuntimeError("Groq LLM not configured: set GROQ_API_KEY")

            messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": prompt}]
            
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=0.7,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    tokens += 1
                    yield chunk.choices[0].delta.content
        finally:
            persist_span(None, "groq.generate_stream", "llm",
                (time.perf_counter() - t0) * 1000,
                {"model": self.model, "tokens": tokens, "prompt_length": len(prompt)})
