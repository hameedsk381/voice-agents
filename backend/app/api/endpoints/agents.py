from datetime import datetime, timezone
from typing import List

import uuid
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.orm import Session

from app.core import database
from app.models import agent as models
from app.orchestration.ultravox_call import merge_ultravox_config
from app.orchestration.websocket_proxy import is_ultravox_runtime
from app.schemas import agent as schemas
from app.services.ultravox_agent_sync import (
    delete_ultravox_agent_for_voise_agent,
    sync_agent_to_ultravox,
)

router = APIRouter()


async def _persist_ultravox_sync(db_agent: models.Agent, db: Session) -> None:
    if not is_ultravox_runtime():
        return
    try:
        uv_id = await sync_agent_to_ultravox(db_agent)
        if uv_id:
            db_agent.config = merge_ultravox_config(
                db_agent.config,
                ultravox_agent_id=uv_id,
                synced_at=datetime.now(timezone.utc).isoformat(),
            )
            db.commit()
            db.refresh(db_agent)
    except Exception as exc:
        logger.warning(f"Ultravox sync deferred for agent {db_agent.id}: {exc}")


@router.post("/", response_model=schemas.Agent)
async def create_agent(agent: schemas.AgentCreate, db: Session = Depends(database.get_db)):
    db_agent = models.Agent(
        id=str(uuid.uuid4()),
        name=agent.name,
        role=agent.role,
        description=agent.description,
        persona=agent.persona,
        language=agent.language,
        tools=agent.tools,
        goals=agent.goals,
        success_criteria=agent.success_criteria,
        failure_conditions=agent.failure_conditions,
        exit_actions=agent.exit_actions,
        is_active=agent.is_active,
        token_limit=agent.token_limit,
        fallback_model=agent.fallback_model,
        organization_id=agent.organization_id,
        config=agent.config,
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    await _persist_ultravox_sync(db_agent, db)
    return db_agent


@router.get("/", response_model=List[schemas.Agent])
def read_agents(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    agents = db.query(models.Agent).offset(skip).limit(limit).all()
    return agents


@router.get("/{agent_id}", response_model=schemas.Agent)
def read_agent(agent_id: str, db: Session = Depends(database.get_db)):
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=schemas.Agent)
async def update_agent(
    agent_id: str,
    agent_update: schemas.AgentUpdate,
    db: Session = Depends(database.get_db),
):
    db_agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    update_data = agent_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_agent, key, value)

    db.commit()
    db.refresh(db_agent)
    await _persist_ultravox_sync(db_agent, db)
    return db_agent


@router.post("/{agent_id}/sync-ultravox", response_model=schemas.Agent)
async def sync_ultravox_agent(agent_id: str, db: Session = Depends(database.get_db)):
    """Push the latest Voise agent config to the linked Ultravox Agent template."""
    if not is_ultravox_runtime():
        raise HTTPException(
            status_code=503,
            detail="Ultravox is not configured. Set ULTRAVOX_API_KEY and VOICE_RUNTIME=ultravox.",
        )

    db_agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    uv_id = await sync_agent_to_ultravox(db_agent)
    if not uv_id:
        raise HTTPException(status_code=502, detail="Ultravox agent sync failed")

    db_agent.config = merge_ultravox_config(
        db_agent.config,
        ultravox_agent_id=uv_id,
        synced_at=datetime.now(timezone.utc).isoformat(),
    )
    db.commit()
    db.refresh(db_agent)
    return db_agent


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, db: Session = Depends(database.get_db)):
    db_agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    await delete_ultravox_agent_for_voise_agent(db_agent)
    db.delete(db_agent)
    db.commit()
    return {"ok": True}


@router.post("/{agent_id}/versions", response_model=schemas.AgentVersion)
def create_agent_version(
    agent_id: str,
    version_data: schemas.AgentVersionCreate,
    db: Session = Depends(database.get_db),
):
    """Create a new snapshot/version of an agent."""
    db_agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    db_version = models.AgentVersion(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        version_number=version_data.version_number,
        persona=version_data.persona,
        tools=version_data.tools,
        policy=version_data.policy,
        success_criteria=version_data.success_criteria,
        failure_conditions=version_data.failure_conditions,
        exit_actions=version_data.exit_actions,
        change_log=version_data.change_log,
        token_limit=version_data.token_limit,
        fallback_model=version_data.fallback_model,
    )
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version


@router.get("/{agent_id}/versions", response_model=List[schemas.AgentVersion])
def get_agent_versions(agent_id: str, db: Session = Depends(database.get_db)):
    """List all versions for an agent."""
    return (
        db.query(models.AgentVersion)
        .filter(models.AgentVersion.agent_id == agent_id)
        .order_by(models.AgentVersion.version_number.desc())
        .all()
    )


@router.post("/{agent_id}/pin/{version_id}")
async def pin_agent_version(
    agent_id: str,
    version_id: str,
    db: Session = Depends(database.get_db),
):
    """Pin the agent to a specific version and re-sync the Ultravox Agent template."""
    db_agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    db_version = db.query(models.AgentVersion).filter(models.AgentVersion.id == version_id).first()

    if not db_agent or not db_version:
        raise HTTPException(status_code=404, detail="Agent or Version not found")

    db_agent.active_version_id = version_id
    db.commit()
    db.refresh(db_agent)

    if is_ultravox_runtime():
        try:
            uv_id = await sync_agent_to_ultravox(
                db_agent,
                active_persona=db_version.persona,
                active_tools=db_version.tools,
            )
            if uv_id:
                db_agent.config = merge_ultravox_config(
                    db_agent.config,
                    ultravox_agent_id=uv_id,
                    synced_at=datetime.now(timezone.utc).isoformat(),
                )
                db.commit()
        except Exception as exc:
            logger.warning(
                f"Ultravox sync after pin failed for agent {agent_id}: {exc}"
            )

    return {"status": "pinned", "version": db_version.version_number}
