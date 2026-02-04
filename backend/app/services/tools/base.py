from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTool(ABC):
    """Base class for all tools that agents can use."""
    
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema format
    requires_approval: bool = False
    
    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """Execute the tool with given parameters and return result as string."""
        pass
    
    def to_schema(self) -> Dict[str, Any]:
        """Convert tool to function calling schema format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
