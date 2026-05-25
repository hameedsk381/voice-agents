"""Agent Registry API — capability registration and discovery."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.core import database
from app.core.deps import get_current_user_required
from app.models.user import User
from app.services.agent_registry_service import AgentRegistryService

router = APIRouter()


class CapabilityCreate(BaseModel):
    agent_id: str
    name: str
    description: str = ""
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}
    cost_per_call: float = 0.0


class CapabilityResponse(BaseModel):
    id: str
    agent_id: str
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    cost_per_call: float

    class Config:
        from_attributes = True


@router.get("/registry", response_model=List[dict])
async def list_registry(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """List all registered agents with their capabilities."""
    service = AgentRegistryService(db)
    return service.list_registry()


@router.get("/capabilities", response_model=List[CapabilityResponse])
async def list_capabilities(
    agent_id: Optional[str] = None,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """List capabilities, optionally filtered by agent."""
    service = AgentRegistryService(db)
    return service.list_capabilities(agent_id=agent_id)


@router.post("/capabilities", response_model=CapabilityResponse, status_code=201)
async def register_capability(
    data: CapabilityCreate,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Register a new capability for an agent."""
    service = AgentRegistryService(db)
    return service.register_capability(
        agent_id=data.agent_id,
        name=data.name,
        description=data.description,
        input_schema=data.input_schema,
        output_schema=data.output_schema,
        cost_per_call=data.cost_per_call,
    )


@router.delete("/capabilities/{cap_id}")
async def delete_capability(
    cap_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = AgentRegistryService(db)
    if not service.delete_capability(cap_id):
        raise HTTPException(status_code=404, detail="Capability not found")
    return {"status": "deleted"}


@router.get("/discover")
async def discover_agent(
    capability: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Find an agent that can handle a given capability."""
    service = AgentRegistryService(db)
    agent = service.find_agent_for_capability(capability)
    if not agent:
        raise HTTPException(status_code=404, detail=f"No agent found for capability '{capability}'")
    return {"agent_id": agent.id, "agent_name": agent.name, "role": agent.role}
