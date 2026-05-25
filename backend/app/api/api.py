from fastapi import APIRouter
from app.api.endpoints import (
    agents,
    orchestrator,
    memory,
    auth,
    monitoring,
    campaigns,
    analytics,
    hitl,
    marketplace,
    telephony,
    voices,
    knowledge,
    ultravox_webhooks,
    workflows,
    observability,
    policy,
    checkpoints,
    agent_registry,
    agent_identity,
    billing,
    organizations,
    phone_numbers,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(orchestrator.router, prefix="/orchestrator", tags=["voice-orchestrator"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge-base"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(hitl.router, prefix="/hitl", tags=["hitl"])
api_router.include_router(marketplace.router, prefix="/marketplace", tags=["marketplace"])
api_router.include_router(telephony.router, prefix="/telephony", tags=["telephony"])
api_router.include_router(voices.router, prefix="/voices", tags=["voices"])
api_router.include_router(
    ultravox_webhooks.router, prefix="/ultravox/webhooks", tags=["ultravox-webhooks"]
)
api_router.include_router(observability.router, prefix="/observability", tags=["observability"])
api_router.include_router(policy.router, prefix="/policy", tags=["policy-engine"])
api_router.include_router(checkpoints.router, prefix="/checkpoints", tags=["durable-execution"])
api_router.include_router(agent_registry.router, prefix="/agent-registry", tags=["agent-registry"])
api_router.include_router(agent_identity.router, prefix="/identity", tags=["agent-identity"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(phone_numbers.router, prefix="/phone-numbers", tags=["phone-numbers"])
