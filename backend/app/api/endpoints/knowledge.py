from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.core import database
from app.schemas import knowledge as schemas
from app.services.knowledge_service import KnowledgeService
from app.models.agent import Agent

router = APIRouter()

@router.post("/{agent_id}", response_model=schemas.Knowledge)
async def add_knowledge(
    agent_id: str,
    knowledge: schemas.KnowledgeCreate,
    db: Session = Depends(database.get_db)
):
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    service = KnowledgeService(db)
    return await service.add_knowledge(
        agent_id=agent_id,
        title=knowledge.title,
        content=knowledge.content,
        data_metadata=knowledge.data_metadata,
        organization_id=agent.organization_id
    )

@router.get("/{agent_id}", response_model=List[schemas.Knowledge])
async def list_knowledge(
    agent_id: str,
    db: Session = Depends(database.get_db)
):
    from app.models.knowledge import AgentKnowledge
    return db.query(AgentKnowledge).filter(AgentKnowledge.agent_id == agent_id).all()

@router.get("/{agent_id}/query", response_model=List[schemas.KnowledgeQueryResult])
async def query_knowledge(
    agent_id: str,
    q: str = Query(...),
    limit: int = 3,
    db: Session = Depends(database.get_db)
):
    service = KnowledgeService(db)
    return await service.query_knowledge(agent_id, q, limit=limit)

@router.delete("/{knowledge_id}")
async def delete_knowledge(
    knowledge_id: str,
    db: Session = Depends(database.get_db)
):
    service = KnowledgeService(db)
    await service.delete_knowledge(knowledge_id)
    return {"status": "deleted"}
