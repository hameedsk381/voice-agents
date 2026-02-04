"""
Analytics service for tracking platform performance and observability.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.models.analytics import CallLog
from app.models.agent import Agent
from app.services.compliance_service import redactor

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    async def log_call_completion(self, session_data: Dict[str, Any]):
        """Saves final session metrics to persistent storage."""
        call_log = CallLog(
            session_id=session_data["session_id"],
            agent_id=session_data["agent_id"],
            caller_id=session_data.get("caller_id"),
            campaign_id=session_data.get("campaign_id"),
            start_time=session_data["start_time"],
            end_time=datetime.utcnow(),
            duration_seconds=session_data.get("duration", 0),
            avg_latency_ms=session_data.get("avg_latency", 0),
            ttfap_ms=session_data.get("ttfap", 0),
            total_turns=session_data.get("turns", 0),
            total_tokens=session_data.get("tokens", 0),
            estimated_cost=session_data.get("cost", 0),
            status=session_data.get("status", "completed"),
            end_reason=session_data.get("reason", "normal"),
            transcript=redactor.redact_transcript(session_data.get("transcript", []))
        )
        self.db.add(call_log)
        self.db.commit()
        return call_log

    async def get_overview_stats(self) -> Dict[str, Any]:
        """Get high-level statistics for the dashboard."""
        total_calls = self.db.query(func.count(CallLog.id)).scalar()
        total_duration = self.db.query(func.sum(CallLog.duration_seconds)).scalar() or 0
        avg_latency = self.db.query(func.avg(CallLog.avg_latency_ms)).scalar() or 0
        total_cost = self.db.query(func.sum(CallLog.estimated_cost)).scalar() or 0
        
        # Success rate
        completed = self.db.query(func.count(CallLog.id)).filter(CallLog.status == "completed").scalar()
        success_rate = (completed / total_calls * 100) if total_calls > 0 else 0
        
        return {
            "total_calls": total_calls,
            "total_minutes": round(total_duration / 60, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "total_cost": round(total_cost, 4),
            "success_rate": round(success_rate, 1)
        }

    async def get_calls_over_time(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get call volume grouped by day."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = self.db.query(
            func.date(CallLog.start_time).label('date'),
            func.count(CallLog.id).label('count')
        ).filter(CallLog.start_time >= start_date)\
         .group_by(func.date(CallLog.start_time))\
         .order_by('date').all()
         
        return [{"date": str(r.date), "count": r.count} for r in results]

    async def get_agent_performance(self) -> List[Dict[str, Any]]:
        """Compare performance across different agents."""
        results = self.db.query(
            Agent.name,
            func.count(CallLog.id).label('calls'),
            func.avg(CallLog.duration_seconds).label('avg_duration'),
            func.avg(CallLog.avg_latency_ms).label('avg_latency')
        ).join(CallLog, Agent.id == CallLog.agent_id)\
         .group_by(Agent.name).all()
         
        return [{
            "name": r.name,
            "calls": r.calls,
            "avg_duration": round(r.avg_duration, 1),
            "avg_latency": round(r.avg_latency, 0)
        } for r in results]
