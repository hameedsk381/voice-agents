import os
import asyncio
import json
from typing import AsyncGenerator, Optional, Tuple, List, Dict, Any
from groq import AsyncGroq
from .base import LLMProvider
from app.core.config import settings

class GroqLLM(LLMProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        if self.api_key:
            self.client = AsyncGroq(api_key=self.api_key)
        else:
            self.client = None

    async def generate_response(self, prompt: str, system_prompt: str, history: list, tools: list = None) -> str:
        if not self.client:
            return f"Mock Groq Response: {prompt}"

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": "llama3-70b-8192",
            "messages": messages,
            "temperature": 0.7,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    async def generate_with_tools(
        self, 
        prompt: str, 
        system_prompt: str, 
        history: list,
        tools: list = None
    ) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
        """
        Generate response that might include tool calls.
        Returns: (text_response, tool_calls)
        """
        if not self.client:
            return f"Mock response to '{prompt}' (no tools in mock)", None

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": "llama-3.3-70b-versatile",  # Best for tool use
            "messages": messages,
            "temperature": 0.3,  # Lower temp for tool calling accuracy
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

    async def generate_stream(self, prompt: str, system_prompt: str, history: list) -> AsyncGenerator[str, None]:
        if not self.client:
            mock_resp = f"This is a simulated Groq response to '{prompt}'."
            for word in mock_resp.split(" "):
                yield word + " "
                await asyncio.sleep(0.05)
            return

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": prompt}]
        
        stream = await self.client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            stream=True,
            temperature=0.7,
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
