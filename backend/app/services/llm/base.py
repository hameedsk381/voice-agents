from abc import ABC, abstractmethod
from typing import AsyncGenerator

class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str, system_prompt: str, history: list) -> str:
        """Generate a complete text response."""
        pass

    @abstractmethod
    async def generate_stream(self, prompt: str, system_prompt: str, history: list) -> AsyncGenerator[str, None]:
        """Generate a streamed text response."""
        pass
