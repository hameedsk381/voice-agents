from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
import json
from app.services.llm.groq_provider import GroqLLM
from app.services.tools.mcp_service import mcp_client

class ToolPlanner:
    """
    Implements Step 2 of 'agents.md': Tool Planning & Sequencing.
    Decides on tool usage and generates conversational 'Plans' for the user.
    """
    
    def __init__(self):
        # Use a reasoning-capable model for planning
        self.planner_llm = GroqLLM(model="llama-3.3-70b-versatile")

    async def generate_plan(
        self, 
        user_input: str, 
        history: List[Dict[str, str]], 
        available_tools: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Analyzes the situation and returns (Plan String, List of Tool Calls).
        Example Plan: "I'll check your order status first, then confirm delivery."
        """
        
        tools_str = json.dumps(available_tools, indent=2)
        
        prompt = f"""
        You are a tool planning assistant for a voice AI.
        
        USER INPUT: {user_input}
        AVAILABLE TOOLS:
        {tools_str}
        
        TASK:
        1. Decide if any tools are needed to satisfy the user request.
        2. If tools are needed, provide a concise, natural 'Plan Statement' (what you will do next).
        3. List the tool calls in sequence.
        
        Respond ONLY in JSON format:
        {{
            "plan_statement": "The conversational statement of what you'll do.",
            "tool_calls": [
                {{"name": "tool_name", "arguments": {{...}}}}
            ]
        }}
        
        If no tools are needed, return an empty tool_calls list and a null plan_statement.
        """
        
        try:
            response_text = await self.planner_llm.generate_response(
                prompt, 
                "You are an expert strategic planner.",
                history
            )
            
            # Cleanup potential markdown
            clean_json = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            return data.get("plan_statement"), data.get("tool_calls", [])
            
        except Exception as e:
            logger.error(f"Tool Planning Failed: {e}")
            return None, []

# Factory
def get_tool_planner():
    return ToolPlanner()
