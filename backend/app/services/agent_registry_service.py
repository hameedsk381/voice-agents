"""Agent Registry — capability registration, discovery, and routing."""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from loguru import logger
from app.models.agent import Agent
from app.models.agent_capability import AgentCapability


class AgentRegistryService:
    def __init__(self, db: Session):
        self.db = db

    # --- Capability CRUD ---

    def register_capability(
        self,
        agent_id: str,
        name: str,
        description: str = "",
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        cost_per_call: float = 0.0,
    ) -> AgentCapability:
        cap = AgentCapability(
            agent_id=agent_id,
            name=name,
            description=description,
            input_schema=input_schema or {},
            output_schema=output_schema or {},
            cost_per_call=cost_per_call,
        )
        self.db.add(cap)
        self.db.commit()
        self.db.refresh(cap)
        logger.info(f"Registered capability '{name}' for agent {agent_id}")
        return cap

    def list_capabilities(
        self, agent_id: Optional[str] = None, organization_id: Optional[str] = None
    ) -> List[AgentCapability]:
        q = self.db.query(AgentCapability)
        if agent_id:
            q = q.filter(AgentCapability.agent_id == agent_id)
        return q.all()

    def delete_capability(self, cap_id: str) -> bool:
        cap = self.db.query(AgentCapability).filter(AgentCapability.id == cap_id).first()
        if not cap:
            return False
        self.db.delete(cap)
        self.db.commit()
        return True

    # --- Discovery ---

    def find_agent_for_capability(
        self, capability_name: str, organization_id: Optional[str] = None
    ) -> Optional[Agent]:
        """Find an active agent registered with a given capability name."""
        q = (
            self.db.query(Agent)
            .join(AgentCapability, Agent.id == AgentCapability.agent_id)
            .filter(AgentCapability.name == capability_name, Agent.is_active == True)
        )
        agent = q.first()
        if agent:
            logger.info(f"Discovered agent '{agent.name}' for capability '{capability_name}'")
        return agent

    def list_registry(self, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return a registry view: agents with their capabilities."""
        q = self.db.query(Agent).filter(Agent.is_active == True).limit(50)
        agents = q.all()
        result = []
        for agent in agents:
            caps = (
                self.db.query(AgentCapability)
                .filter(AgentCapability.agent_id == agent.id)
                .all()
            )
            result.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "role": agent.role,
                "description": agent.description,
                "capabilities": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "description": c.description,
                        "input_schema": c.input_schema,
                        "output_schema": c.output_schema,
                        "cost_per_call": c.cost_per_call,
                    }
                    for c in caps
                ],
            })
        return result
