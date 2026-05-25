"""
API endpoints for multi-layer memory management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any
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


# --- Working Memory Schemas ---

class WorkingMemorySetRequest(BaseModel):
    session_id: str
    agent_id: str
    key: str
    value: Any
    ttl_seconds: Optional[int] = None


class WorkingMemoryResponse(BaseModel):
    session_id: str
    key: str
    value: Any


# --- Procedural Memory Schemas ---

class ProcedureStep(BaseModel):
    action: str
    description: str
    tool: Optional[str] = None
    params: Optional[dict] = None


class ProcedureStoreRequest(BaseModel):
    agent_id: str
    name: str
    steps: List[dict]
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class ProcedureResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    steps: List[dict]
    tags: List[str]
    updated_at: str


# --- Governance Schemas ---

class ForgetRequest(BaseModel):
    user_id: str
    key: Optional[str] = None
    category: Optional[str] = None


class ConsentRequest(BaseModel):
    user_id: str
    status: str  # granted, withdrawn, unknown


# ==================== LONG-TERM MEMORY ====================

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

    db.query(MemoryItem).filter(MemoryItem.user_id == user_id).delete()
    db.query(ConversationSummary).filter(ConversationSummary.user_id == user_id).delete()
    db.query(UserProfile).filter(UserProfile.user_id == user_id).delete()

    db.commit()

    logger.info(f"Deleted all memories for user {user_id}")

    return {"status": "deleted", "user_id": user_id}


# ==================== WORKING MEMORY ====================

@router.post("/working/set", response_model=dict)
async def set_working_memory(
    request: WorkingMemorySetRequest,
    db: Session = Depends(database.get_db)
):
    """Store ephemeral working memory for an active session."""
    service = get_memory_service(db)
    result = await service.set_working(
        agent_id=request.agent_id,
        session_id=request.session_id,
        key=request.key,
        value=request.value,
        ttl_seconds=request.ttl_seconds
    )
    return {"status": "stored", "session_id": request.session_id, "key": request.key}


@router.get("/working/{session_id}", response_model=dict)
async def get_working_memory(
    session_id: str,
    key: Optional[str] = Query(None),
    db: Session = Depends(database.get_db)
):
    """Retrieve working memory for a session."""
    service = get_memory_service(db)
    data = await service.get_working(session_id, key)
    return {"session_id": session_id, "data": data}


@router.delete("/working/{session_id}")
async def clear_working_memory(
    session_id: str,
    db: Session = Depends(database.get_db)
):
    """Clear working memory for a finished session."""
    service = get_memory_service(db)
    await service.clear_working(session_id)
    return {"status": "cleared", "session_id": session_id}


# ==================== PROCEDURAL MEMORY ====================

@router.post("/procedures", response_model=ProcedureResponse)
async def store_procedure(
    request: ProcedureStoreRequest,
    db: Session = Depends(database.get_db)
):
    """Store or update a procedure for an agent."""
    service = get_memory_service(db)
    result = await service.store_procedure(
        agent_id=request.agent_id,
        name=request.name,
        steps=request.steps,
        description=request.description,
        tags=request.tags
    )
    return ProcedureResponse(
        id=result.id,
        name=result.name,
        description=result.description,
        steps=result.steps,
        tags=result.tags or [],
        updated_at=result.updated_at.isoformat() if result.updated_at else ""
    )


@router.get("/procedures/{agent_id}", response_model=List[ProcedureResponse])
async def recall_procedures(
    agent_id: str,
    name: Optional[str] = Query(None),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    db: Session = Depends(database.get_db)
):
    """Recall procedures for an agent."""
    service = get_memory_service(db)
    tag_list = tags.split(",") if tags else None
    results = await service.recall_procedure(agent_id, name=name, tags=tag_list)
    return [
        ProcedureResponse(
            id=r["id"],
            name=r["name"],
            description=r.get("description"),
            steps=r["steps"],
            tags=r.get("tags", []),
            updated_at=r["updated_at"]
        )
        for r in results
    ]


@router.delete("/procedures/{agent_id}/{name}")
async def delete_procedure(
    agent_id: str,
    name: str,
    db: Session = Depends(database.get_db)
):
    """Delete a specific procedure."""
    service = get_memory_service(db)
    await service.delete_procedure(agent_id, name)
    return {"status": "deleted", "agent_id": agent_id, "name": name}


# ==================== GOVERNANCE ====================

@router.post("/governance/forget")
async def forget_memories(
    request: ForgetRequest,
    db: Session = Depends(database.get_db)
):
    """GDPR-style deletion of specific memories."""
    service = get_memory_service(db)
    count = await service.forget(
        user_id=request.user_id,
        key=request.key,
        category=request.category
    )
    return {"status": "forgotten", "user_id": request.user_id, "count": count}


@router.post("/governance/do-not-remember")
async def mark_do_not_remember(
    request: ForgetRequest,
    db: Session = Depends(database.get_db)
):
    """Flag memories as 'do not remember' (preserves data but hides from context)."""
    service = get_memory_service(db)
    await service.mark_do_not_remember(request.user_id, key=request.key)
    return {"status": "marked", "user_id": request.user_id}


@router.post("/governance/consent")
async def set_consent(
    request: ConsentRequest,
    db: Session = Depends(database.get_db)
):
    """Set or update user consent status for memory storage."""
    if request.status not in ("granted", "withdrawn", "unknown"):
        raise HTTPException(status_code=400, detail="Status must be 'granted', 'withdrawn', or 'unknown'")
    service = get_memory_service(db)
    await service.set_user_consent(request.user_id, request.status)
    return {"status": "updated", "user_id": request.user_id, "consent": request.status}


@router.post("/governance/ttl-cleanup")
async def run_ttl_cleanup(
    db: Session = Depends(database.get_db)
):
    """Manually trigger TTL cleanup of expired memories."""
    service = get_memory_service(db)
    count = await service.run_ttl_cleanup()
    return {"status": "cleanup_complete", "removed_count": count}
