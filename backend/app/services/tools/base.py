from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ToolResult:
    """Result of a tool execution with confidence scoring."""
    result: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """Base class for all tools that agents can use."""
    
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema format
    requires_approval: bool = False
    preconditions: list[str] = []
    postconditions: list[str] = []
    cost_per_call: float = 0.0
    # When True, the executor injects _db (Session) and _session_id (str) into execute().
    needs_context: bool = False
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters. Returns ToolResult with confidence."""
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
