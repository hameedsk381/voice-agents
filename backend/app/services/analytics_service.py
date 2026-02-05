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
from app.services.llm.groq_provider import GroqLLM
import json
import hashlib
import hmac
from app.core.config import settings

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.classifier_llm = GroqLLM(model="llama-3.1-8b-instant")

    async def log_call_completion(self, session_data: Dict[str, Any], agent: Optional[Agent] = None):
        """Saves final session metrics to persistent storage."""
        transcript = session_data.get("transcript", [])
        redacted_transcript = redactor.redact_transcript(transcript)
        
        # Determine Outcome
        outcome = "NEUTRAL"
        outcome_reason = "No criteria matched"
        
        if agent:
            outcome, outcome_reason = await self.classify_outcome(redacted_transcript, agent)
            
        # Generate Immutable Signature (Elite Compliance Feature)
        signature = self.sign_transcript(redacted_transcript, session_data["session_id"])

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
            organization_id=session_data.get("org_id"), # Added for Multitenancy
            status=session_data.get("status", "completed"),
            end_reason=session_data.get("reason", "normal"),
            outcome=outcome,
            outcome_reason=outcome_reason,
            transcript=redacted_transcript,
            signature=signature
        )
        self.db.add(call_log)
        self.db.commit()
        return call_log

    def sign_transcript(self, transcript: List[Dict[str, Any]], session_id: str) -> str:
        """Creates an HMAC signature of the transcript to prevent tampering."""
        text = json.dumps(transcript, sort_keys=True) + session_id
        secret = (settings.SECRET_KEY or "enterprise-secret").encode()
        return hmac.new(secret, text.encode(), hashlib.sha256).hexdigest()

    async def classify_outcome(self, transcript: List[Dict[str, Any]], agent: Agent) -> tuple[str, str]:
        """Uses LLM to classify the call outcome based on agent goals."""
        if not transcript:
            return "NEUTRAL", "Empty transcript"
            
        success_criteria = agent.success_criteria or []
        failure_conditions = agent.failure_conditions or []
        
        transcript_text = "\n".join([f"{t['role'].upper()}: {t['content']}" for t in transcript])
        
        prompt = f"""
        Analyze the following voice call transcript and determine if the call was a SUCCESS, FAILURE, or NEUTRAL.
        
        AGENT GOALS: {agent.goals}
        SUCCESS CRITERIA: {success_criteria}
        FAILURE CONDITIONS: {failure_conditions}
        
        TRANSCRIPT:
        {transcript_text}
        
        Return your analysis STRICTLY in JSON format:
        {{
            "outcome": "SUCCESS|FAILURE|NEUTRAL",
            "reason": "Brief explanation of why this outcome was chosen"
        }}
        """
        
        try:
            response_text = await self.classifier_llm.generate_response(
                prompt, 
                "You are an expert call quality analyst.",
                []
            )
            # Cleanup potential markdown
            clean_json = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            return data.get("outcome", "NEUTRAL"), data.get("reason", "Analyzed by LLM")
        except Exception as e:
            from loguru import logger
            logger.error(f"Outcome classification failed: {e}")
            return "NEUTRAL", f"Error during analysis: {str(e)}"

    async def get_overview_stats(self) -> Dict[str, Any]:
        """Get high-level statistics for the dashboard."""
        total_calls = self.db.query(func.count(CallLog.id)).scalar()
        total_duration = self.db.query(func.sum(CallLog.duration_seconds)).scalar() or 0
        avg_latency = self.db.query(func.avg(CallLog.avg_latency_ms)).scalar() or 0
        total_cost = self.db.query(func.sum(CallLog.estimated_cost)).scalar() or 0
        
        # Success rate (based on AI outcome classification)
        successful_calls = self.db.query(func.count(CallLog.id)).filter(CallLog.outcome == "SUCCESS").scalar()
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        
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

    async def get_compliance_report(self, session_id: str) -> Dict[str, Any]:
        """Generate a summarized compliance audit report for a session."""
        from app.models.compliance import AuditLog
        audits = self.db.query(AuditLog).filter(AuditLog.session_id == session_id).all()
        
        violations = []
        for a in audits:
            if not a.is_compliant:
                violations.extend(a.violations)
                
        return {
            "session_id": session_id,
            "is_compliant": len(violations) == 0,
            "risk_score": max([a.risk_score for a in audits] if audits else [0]),
            "violation_count": len(violations),
            "details": violations,
            "turns_audited": len(audits)
        }
    async def get_shadow_stats(self) -> Dict[str, Any]:
        """Get statistics for shadow model comparisons."""
        from app.models.analytics import ShadowLog
        
        avg_sim = self.db.query(func.avg(ShadowLog.similarity_score)).scalar() or 0
        total_shadow_runs = self.db.query(func.count(ShadowLog.id)).scalar()
        avg_primary_lat = self.db.query(func.avg(ShadowLog.primary_latency_ms)).scalar() or 0
        avg_shadow_lat = self.db.query(func.avg(ShadowLog.shadow_latency_ms)).scalar() or 0
        
        # Performance by model pair
        model_pairs = self.db.query(
            ShadowLog.primary_model,
            ShadowLog.shadow_model,
            func.avg(ShadowLog.similarity_score).label("avg_similarity"),
            func.count(ShadowLog.id).label("count")
        ).group_by(ShadowLog.primary_model, ShadowLog.shadow_model).all()
        
        return {
            "avg_similarity": round(avg_sim, 4),
            "total_runs": total_shadow_runs,
            "avg_primary_latency": round(avg_primary_lat, 2),
            "avg_shadow_latency": round(avg_shadow_lat, 2),
            "latency_savings": round(avg_primary_lat - avg_shadow_lat, 2),
            "model_performance": [
                {
                    "primary": m.primary_model,
                    "shadow": m.shadow_model,
                    "similarity": round(m.avg_similarity, 4),
                    "runs": m.count
                } for m in model_pairs
            ]
        }
        
