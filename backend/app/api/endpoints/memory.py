"""
API endpoints for memory management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core import database
from app.services.memory import get_memory_service
from loguru import logger

router = APIRouter()


class MemoryCreate(BaseModel):
    user_id: str
    category: str
    key: str
    value: str
    confidence: float = 1.0


class MemoryResponse(BaseModel):
    id: str
    category: str
    key: str
    value: str
    confidence: float
    relevance: Optional[float] = None


class MemorySearchRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    category: Optional[str] = None
    limit: int = 10


class UserContextResponse(BaseModel):
    user_id: str
    context: str
    memory_count: int


@router.post("/memorize", response_model=MemoryResponse)
async def create_memory(
    memory: MemoryCreate,
    db: Session = Depends(database.get_db)
):
    """Store a memory fact for a user."""
    service = get_memory_service(db)
    
    result = await service.memorize(
        user_id=memory.user_id,
        category=memory.category,
        key=memory.key,
        value=memory.value,
        confidence=memory.confidence
    )
    
    return MemoryResponse(
        id=result.id,
        category=result.category,
        key=result.key,
        value=result.value,
        confidence=result.confidence
    )


@router.post("/retrieve", response_model=List[MemoryResponse])
async def retrieve_memories(
    request: MemorySearchRequest,
    db: Session = Depends(database.get_db)
):
    """Semantic search across memories."""
    service = get_memory_service(db)
    
    results = await service.retrieve(
        query=request.query,
        user_id=request.user_id,
        category=request.category,
        limit=request.limit
    )
    
    return [
        MemoryResponse(
            id=r["id"],
            category=r["category"],
            key=r["key"],
            value=r["value"],
            confidence=r["confidence"],
            relevance=r.get("relevance")
        )
        for r in results
    ]


@router.get("/user/{user_id}", response_model=dict)
async def get_user_memories(
    user_id: str,
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    db: Session = Depends(database.get_db)
):
    """Get all memories for a user, grouped by category."""
    service = get_memory_service(db)
    
    category_list = categories.split(",") if categories else None
    
    memories = await service.get_user_memories(user_id, category_list)
    
    return {
        "user_id": user_id,
        "memories": memories,
        "total_count": sum(len(items) for items in memories.values())
    }


@router.get("/context/{user_id}", response_model=UserContextResponse)
async def get_user_context(
    user_id: str,
    db: Session = Depends(database.get_db)
):
    """Get context string for a user (for agent prompts)."""
    service = get_memory_service(db)
    
    context = await service.get_context_for_call(user_id)
    memories = await service.get_user_memories(user_id)
    
    return UserContextResponse(
        user_id=user_id,
        context=context,
        memory_count=sum(len(items) for items in memories.values())
    )


@router.delete("/user/{user_id}")
async def delete_user_memories(
    user_id: str,
    db: Session = Depends(database.get_db)
):
    """Delete all memories for a user (GDPR compliance)."""
    from app.models.memory import MemoryItem, ConversationSummary, UserProfile
    
    # Delete all user data
    db.query(MemoryItem).filter(MemoryItem.user_id == user_id).delete()
    db.query(ConversationSummary).filter(ConversationSummary.user_id == user_id).delete()
    db.query(UserProfile).filter(UserProfile.user_id == user_id).delete()
    
    db.commit()
    
    logger.info(f"Deleted all memories for user {user_id}")
    
    return {"status": "deleted", "user_id": user_id}
