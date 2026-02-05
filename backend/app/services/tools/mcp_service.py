import json
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from loguru import logger
from app.core.config import settings

class MCPClient:
    """
    A simplified MCP (Model Context Protocol) client for the voice platform.
    Connects to external MCP servers to discover and execute tools.
    """
    
    def __init__(self, server_url: str = None):
        self.server_url = server_url or getattr(settings, "MCP_SERVER_URL", "http://localhost:8002")
        self.httpx_client = httpx.AsyncClient(timeout=30.0)
        self._tools_cache = []

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        try:
            # MCP Standard: tools/list
            response = await self.httpx_client.post(
                f"{self.server_url}/tools/list",
                json={"protocol_version": "2024-11-05"}
            )
            data = response.json()
            self._tools_cache = data.get("tools", [])
            return self._tools_cache
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {e}")
            # Fallback to empty if server not reachable
            return []

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool via the MCP server."""
        try:
            # MCP Standard: tools/call
            logger.info(f"Calling MCP Tool: {name} with {arguments}")
            response = await self.httpx_client.post(
                f"{self.server_url}/tools/call",
                json={
                    "name": name,
                    "arguments": arguments,
                    "protocol_version": "2024-11-05"
                }
            )
            data = response.json()
            
            # MCP response usually comes in a 'content' list
            content = data.get("content", [])
            if content and isinstance(content, list):
                return str(content[0].get("text", "Tool executed with no output."))
            return str(data.get("result", "Tool executed."))
            
        except Exception as e:
            logger.error(f"MCP Tool Execution Failed: {e}")
            return f"Error executing tool: {str(e)}"

    async def close(self):
        await self.httpx_client.aclose()

# Singleton instance
mcp_client = MCPClient()
