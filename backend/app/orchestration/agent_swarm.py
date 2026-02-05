from typing import List, Dict, Any, Optional
from app.services.llm.groq_provider import GroqLLM
from app.models.agent import Agent
from sqlalchemy.orm import Session
from loguru import logger

class SwarmOrchestrator:
    """
    Manages a collection of specialized agents to solve complex tasks.
    The "Brain" that decides which "Hand" to use.
    """
    
    def __init__(self, db: Session, supervisor_agent: Agent):
        self.db = db
        self.supervisor = supervisor_agent
        self.llm = GroqLLM()

    async def route_task(self, user_input: str, history: List[Dict[str, str]], pool: List[Agent]) -> Optional[Agent]:
        """
        Analyze input and decide which specialized agent in the pool should handle it.
        """
        if not pool:
            return self.supervisor

        agent_labels = "\n".join([f"- {a.id}: {a.name} ({a.role}) - {a.description}" for a in pool])
        
        prompt = f"""
You are a Supervisor Dispatcher for a voice AI swarm.
Analyze the user's latest input and determine which specialized worker agent is best suited to handle the request.

AVAILABLE AGENTS:
{agent_labels}
- SUPERVISOR: Keep the task with the current supervisor agent.

USER INPUT: "{user_input}"

Respond with ONLY the ID of the selected agent or "SUPERVISOR".
"""
        response = await self.llm.generate_response(prompt, "You are an elite dispatcher.", history)
        selected_id = response.strip()

        if selected_id == "SUPERVISOR":
            return self.supervisor
            
        for agent in pool:
            if agent.id == selected_id:
                logger.info(f"Swarm: Delegating task to {agent.name}")
                return agent
                
        return self.supervisor

    async def discover_and_hire(self, task_query: str) -> Optional[Agent]:
        """
        Peak Agentic Feature: Autonomous capability discovery.
        Searches all active agents in the organization for capabilities matching the task.
        """
        logger.info(f"Swarm: Attempting autonomous discovery for task: {task_query}")
        
        # 1. Broad fetch of all active agents
        all_agents = self.db.query(Agent).filter(Agent.is_active == True).all()
        
        if not all_agents:
            return None
            
        # 2. Use LLM to find the best match based on descriptions and goals
        agent_catalog = "\n".join([f"- {a.id}: {a.name} | Role: {a.role} | Desc: {a.description} | Goals: {a.goals}" for a in all_agents])
        
        prompt = f"""
        TASK: "{task_query}"
        
        CATALOG OF AVAILABLE AGENT CAPABILITIES:
        {agent_catalog}
        
        Which agent from the catalog is best suited to handle this task? 
        Respond with ONLY the Agent ID. If no agent is a good fit, respond "NONE".
        """
        
        match_id = await self.llm.generate_response(prompt, "System Discovery Engine", [])
        match_id = match_id.strip()
        
        if match_id == "NONE" or len(match_id) < 10: # Simple heuristic for bad/short responses
            return None
            
        for a in all_agents:
            if a.id == match_id:
                logger.info(f"Swarm: Discovered and 'hired' agent {a.name} for capability: {task_query}")
                return a
                
        return None
