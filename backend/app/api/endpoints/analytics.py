"""
Analytics API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core import database
from app.core.deps import get_current_user_required
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/overview")
async def get_analytics_overview(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = AnalyticsService(db)
    return await service.get_overview_stats()

@router.get("/daily-trends")
async def get_daily_trends(
    days: int = 7,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = AnalyticsService(db)
    return await service.get_calls_over_time(days)

@router.get("/agent-performance")
async def get_agent_analytics(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    service = AnalyticsService(db)
    return await service.get_agent_performance()

@router.get("/")
async def get_logs(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    from app.models.analytics import CallLog
    from app.models.agent import Agent
    
    # Query logs with agent names
    logs = db.query(
        CallLog,
        Agent.name.label("agent_name")
    ).outerjoin(Agent, CallLog.agent_id == Agent.id)\
     .order_by(CallLog.start_time.desc())\
     .offset(skip).limit(limit).all()
    
    # Format response
    result = []
    for log, agent_name in logs:
        log_dict = {c.name: getattr(log, c.name) for c in log.__table__.columns}
        log_dict["agent_name"] = agent_name or "Unknown Agent"
        result.append(log_dict)
        
    return result

@router.get("/recent-calls")
async def get_recent_calls(
    limit: int = 10,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db)
):
    from app.models.analytics import CallLog
    calls = db.query(CallLog).order_by(CallLog.start_time.desc()).limit(limit).all()
    return calls
