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
from app.core.metrics import calls_total, call_duration_seconds, cost_total
from app.services.usage_service import UsageService
import json
import hashlib
import hmac
from app.core.config import settings

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.classifier_llm = GroqLLM(model="llama-3.1-8b-instant")
        self.usage = UsageService(db)

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

        # Prometheus metrics
        calls_total.labels(agent_id=session_data["agent_id"], outcome=outcome).inc()
        call_duration_seconds.labels(agent_id=session_data["agent_id"]).observe(session_data.get("duration", 0))
        cost_total.labels(model=session_data.get("model_name", "unknown")).inc(session_data.get("cost", 0))

        # Annotate with checkpoint metadata if available
        metadata = dict(session_data.get("metadata") or {})
        try:
            from app.services.checkpoint_service import CheckpointService
            ckpt = CheckpointService(self.db).load_latest(session_data["session_id"])
            if ckpt:
                metadata["checkpoint_turns"] = ckpt.turn_index
                metadata["checkpoint_id"] = ckpt.id
                metadata["recovered"] = True
        except Exception:
            pass

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
            organization_id=session_data.get("org_id"),
            status=session_data.get("status", "completed"),
            end_reason=session_data.get("reason", "normal"),
            outcome=outcome,
            outcome_reason=outcome_reason,
            transcript=redacted_transcript,
            metadata_json=metadata,
            signature=signature
        )
        self.db.add(call_log)

        # Record usage metering
        org_id = session_data.get("org_id")
        if org_id:
            try:
                self.usage.record_call_usage(
                    organization_id=org_id,
                    session_id=session_data["session_id"],
                    agent_id=session_data["agent_id"],
                    duration_seconds=session_data.get("duration", 0),
                    stt_seconds=session_data.get("stt_seconds", 0),
                    tts_seconds=session_data.get("tts_seconds", 0),
                    llm_tokens=session_data.get("tokens", 0),
                    tool_calls=session_data.get("tool_calls", 0),
                )
            except Exception:
                pass

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
    async def get_kpi_dashboard(self, org_id: Optional[str] = None) -> Dict[str, Any]:
        """Comprehensive KPI dashboard data with business metrics."""
        query = self.db.query(func.count(CallLog.id))
        if org_id:
            query = query.filter(CallLog.organization_id == org_id)
        total_calls = query.scalar()

        filters = {}
        if org_id:
            filters["organization_id"] = org_id

        def _q():
            q = self.db.query(CallLog)
            if org_id:
                q = q.filter(CallLog.organization_id == org_id)
            return q

        total_duration = _q().with_entities(func.sum(CallLog.duration_seconds)).scalar() or 0
        avg_latency = _q().with_entities(func.avg(CallLog.avg_latency_ms)).scalar() or 0
        total_cost = _q().with_entities(func.sum(CallLog.estimated_cost)).scalar() or 0
        total_tokens = _q().with_entities(func.sum(CallLog.total_tokens)).scalar() or 0
        total_turns = _q().with_entities(func.sum(CallLog.total_turns)).scalar() or 0

        # Outcome breakdown
        success_count = _q().filter(CallLog.outcome == "SUCCESS").count()
        failure_count = _q().filter(CallLog.outcome == "FAILURE").count()
        neutral_count = _q().filter(CallLog.outcome == "NEUTRAL").count()

        # Abandoned / failed calls
        abandoned = _q().filter(
            CallLog.status.in_(["failed", "error"])
        ).count()
        short_calls = _q().filter(
            CallLog.duration_seconds < 15,
            CallLog.status != "failed",
        ).count()

        # Completed calls (for AHT)
        completed = _q().filter(CallLog.status == "completed").count()
        aht_query = _q().filter(CallLog.status == "completed").with_entities(
            func.avg(CallLog.duration_seconds)
        ).scalar() or 0

        # Average turns per completed call
        avg_turns = _q().filter(CallLog.status == "completed").with_entities(
            func.avg(CallLog.total_turns)
        ).scalar() or 0

        cost_per_call = round(total_cost / total_calls, 4) if total_calls > 0 else 0
        aht_seconds = round(aht_query, 1)
        abandonment_rate = round(
            ((abandoned + short_calls) / total_calls * 100), 1
        ) if total_calls > 0 else 0
        success_rate = round(
            (success_count / total_calls * 100), 1
        ) if total_calls > 0 else 0

        return {
            "total_calls": total_calls,
            "total_minutes": round(total_duration / 60, 2),
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "avg_latency_ms": round(avg_latency, 2),
            "cost_per_call": cost_per_call,
            "avg_handle_time_sec": aht_seconds,
            "avg_turns_per_call": round(avg_turns, 1),
            "success_rate": success_rate,
            "abandonment_rate": abandonment_rate,
            "outcome_breakdown": {
                "success": success_count,
                "failure": failure_count,
                "neutral": neutral_count,
            },
        }

    async def get_peak_hours(self, org_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get call volume distribution by hour of day."""
        q = self.db.query(
            extract('hour', CallLog.start_time).label('hour'),
            func.count(CallLog.id).label('count')
        )
        if org_id:
            q = q.filter(CallLog.organization_id == org_id)
        results = q.group_by(extract('hour', CallLog.start_time))\
                   .order_by('hour').all()

        hours = {h: 0 for h in range(24)}
        for r in results:
            hours[int(r.hour)] = r.count

        peak_hour = max(hours, key=hours.get)
        return {
            "distribution": [{"hour": h, "count": c} for h, c in hours.items()],
            "peak_hour": peak_hour,
            "peak_volume": hours[peak_hour],
        }

    async def get_call_quality(self, org_id: Optional[str] = None) -> Dict[str, Any]:
        """Compute call quality score from latency, duration, turns, and outcome."""
        def _q():
            q = self.db.query(CallLog)
            if org_id:
                q = q.filter(CallLog.organization_id == org_id)
            return q

        total = _q().count()
        if total == 0:
            return {"score": 0, "grade": "N/A", "latency_grade": "N/A", "turns_grade": "N/A"}

        avg_lat = float(_q().with_entities(func.avg(CallLog.avg_latency_ms)).scalar() or 0)
        avg_turns = float(_q().with_entities(func.avg(CallLog.total_turns)).scalar() or 0)
        success_rate = _q().filter(CallLog.outcome == "SUCCESS").count() / total

        # Latency score (0-100): lower is better, penalty above 500ms
        lat_score = max(0, 100 - (avg_lat / 500 * 100)) if avg_lat > 0 else 100
        # Turns score (0-100): 5-15 turns is ideal
        turns_score = 100 - min(abs(avg_turns - 10) * 5, 100) if avg_turns > 0 else 100
        # Outcome score
        outcome_score = success_rate * 100

        overall = round(lat_score * 0.3 + turns_score * 0.2 + outcome_score * 0.5, 1)

        def grade(s):
            if s >= 90: return "A"
            if s >= 75: return "B"
            if s >= 60: return "C"
            if s >= 40: return "D"
            return "F"

        return {
            "score": overall,
            "grade": grade(overall),
            "latency_ms": round(avg_lat, 0),
            "latency_grade": grade(lat_score),
            "avg_turns": round(avg_turns, 1),
            "turns_grade": grade(turns_score),
            "outcome_score": round(outcome_score, 1),
        }

    async def get_weekly_trend(self, org_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get daily call volume, duration, and cost for the last 14 days."""
        start = datetime.utcnow() - timedelta(days=14)
        q = self.db.query(
            func.date(CallLog.start_time).label('date'),
            func.count(CallLog.id).label('calls'),
            func.sum(CallLog.duration_seconds).label('total_seconds'),
            func.sum(CallLog.estimated_cost).label('total_cost'),
            func.avg(CallLog.avg_latency_ms).label('avg_latency'),
        ).filter(CallLog.start_time >= start)
        if org_id:
            q = q.filter(CallLog.organization_id == org_id)
        results = q.group_by(func.date(CallLog.start_time)).order_by('date').all()

        return [
            {
                "date": str(r.date),
                "calls": r.calls,
                "total_minutes": round((r.total_seconds or 0) / 60, 1),
                "total_cost": round(r.total_cost or 0, 4),
                "avg_latency_ms": round(r.avg_latency or 0, 0),
            }
            for r in results
        ]

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
        
