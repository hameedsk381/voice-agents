import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import database
from app.core.config import settings
from app.core.deps import get_current_user_required
from app.models import agent as models
from app.models.user import User
from app.orchestration.agent_config import resolve_active_agent_config
from app.schemas.livekit import LiveKitTokenRequest, LiveKitTokenResponse

router = APIRouter()


@router.post("/token/{agent_id}", response_model=LiveKitTokenResponse, status_code=201)
async def create_livekit_token(
    agent_id: str,
    body: LiveKitTokenRequest | None = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user_required),
):
    """Create a LiveKit participant token and explicitly dispatch the configured agent worker."""
    if not settings.LIVEKIT_URL or not settings.LIVEKIT_API_KEY or not settings.LIVEKIT_API_SECRET:
        raise HTTPException(
            status_code=500,
            detail="LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET must be configured",
        )

    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    body = body or LiveKitTokenRequest()
    room_name = body.room_name or f"voise-{agent_id}-{uuid.uuid4().hex[:12]}"
    participant_identity = body.participant_identity or f"user-{current_user.id}-{uuid.uuid4().hex[:8]}"
    participant_name = body.participant_name or current_user.email or "User"
    language = body.language or agent.language or "en-IN"
    voice = body.voice or settings.LIVEKIT_TTS_VOICE

    active_persona, active_tools, active_policy_raw = resolve_active_agent_config(db, agent)
    dispatch_metadata = {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "organization_id": agent.organization_id,
        "caller_id": body.caller_id,
        "language": language,
        "voice": voice,
        "persona": active_persona or agent.persona or "",
        "tools": active_tools or [],
        "policy": active_policy_raw,
    }

    try:
        from livekit import api

        if body.room_config is not None:
            from google.protobuf.json_format import ParseDict

            room_config = ParseDict(body.room_config, api.RoomConfiguration())
        else:
            room_config = api.RoomConfiguration(
                agents=[
                    api.RoomAgentDispatch(
                        agent_name=settings.LIVEKIT_AGENT_NAME,
                        metadata=json.dumps(dispatch_metadata),
                    )
                ]
            )

        token = (
            api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
            .with_identity(participant_identity)
            .with_name(participant_name)
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                    can_publish_data=True,
                )
            )
            .with_room_config(room_config)
        )

        participant_attributes = {
            "user.language": language,
            "voise.agent_id": agent_id,
            **(body.participant_attributes or {}),
        }
        token = token.with_attributes(participant_attributes)

        if body.participant_metadata:
            token = token.with_metadata(body.participant_metadata)

        return LiveKitTokenResponse(
            server_url=settings.LIVEKIT_URL,
            participant_token=token.to_jwt(),
            room_name=room_name,
            agent_name=settings.LIVEKIT_AGENT_NAME,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate LiveKit token: {exc}") from exc
