from abc import ABC, abstractmethod

class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Convert text to audio bytes."""
        pass
        
    @abstractmethod
    async def synthesize_stream(self, text_iterator) -> bytes:
         """Consume text stream and yield audio bytes."""
         pass
