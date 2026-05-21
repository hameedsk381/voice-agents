"""Resolve active persona/tools for an agent (pinned version or A/B weights)."""

import random
from typing import Any, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import agent as models


def resolve_active_agent_config(
    db: Session,
    agent: models.Agent,
) -> Tuple[Optional[str], Optional[List[Any]], Optional[Any]]:
    """
    Returns (persona, tools, policy) — policy is raw dict or ConversationPolicy-ready object.
    """
    active_persona: Optional[str] = agent.persona
    active_tools: Optional[List[Any]] = agent.tools
    active_policy = None

    versions = (
        db.query(models.AgentVersion)
        .filter(
            models.AgentVersion.agent_id == agent.id,
            models.AgentVersion.weight > 0,
        )
        .all()
    )
    if versions:
        total_weight = sum(v.weight for v in versions)
        if total_weight > 0:
            rand_val = random.randint(1, 100)
            cumulative = 0
            for version in versions:
                cumulative += version.weight
                if rand_val <= cumulative:
                    active_persona = version.persona
                    active_tools = version.tools
                    active_policy = version.policy
                    break
    elif agent.active_version_id:
        version = (
            db.query(models.AgentVersion)
            .filter(models.AgentVersion.id == agent.active_version_id)
            .first()
        )
        if version:
            active_persona = version.persona
            active_tools = version.tools
            active_policy = version.policy

    return active_persona, active_tools, active_policy
