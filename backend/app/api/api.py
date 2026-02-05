from fastapi import APIRouter
from app.api.endpoints import agents, orchestrator, memory, auth, monitoring, campaigns, analytics, hitl, marketplace, telephony, voices, knowledge

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(orchestrator.router, prefix="/orchestrator", tags=["voice-orchestrator"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge-base"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(hitl.router, prefix="/hitl", tags=["hitl"])
api_router.include_router(marketplace.router, prefix="/marketplace", tags=["marketplace"])
api_router.include_router(telephony.router, prefix="/telephony", tags=["telephony"])
api_router.include_router(voices.router, prefix="/voices", tags=["voices"])
