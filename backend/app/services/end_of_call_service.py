"""
End-of-Call Intelligence service.
After a call ends: classify outcome, estimate satisfaction,
generate structured summary, schedule next steps, write memories,
and tag for human review when needed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from loguru import logger
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.orchestration.agent_orchestrator import AgentContext


@dataclass
class CallOutcome:
    label: str  # success, failure, neutral, escalated
    confidence: float
    reason: str


@dataclass
class SatisfactionEstimate:
    score: float  # 0.0 to 1.0
    confidence: float
    signals: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NextStep:
    action: str
    description: str
    due_by: Optional[str] = None
    assigned_to: Optional[str] = None


@dataclass
class CallSummary:
    outcome: CallOutcome
    satisfaction: SatisfactionEstimate
    summary_text: str
    key_points: List[str]
    next_steps: List[NextStep]
    requires_human_review: bool = False
    human_review_reason: Optional[str] = None


class EndOfCallService:
    """
    Aggregates all end-of-call intelligence into a structured summary.
    """
    def __init__(self, db: Session, llm_service=None):
        self.db = db
        self.llm = llm_service
        self.sentiment_history: List[float] = []

    async def analyze(
        self,
        transcript: List[Dict[str, str]],
        context: Optional[AgentContext] = None,
        agent: Optional[Agent] = None,
    ) -> CallSummary:
        """
        Full end-of-call analysis pipeline.
        """
        outcome = await self._classify_outcome(transcript, agent)
        satisfaction = self._estimate_satisfaction(transcript, context)
        summary_text, key_points = await self._generate_summary(transcript)
        next_steps = self._schedule_next_steps(outcome, summary_text)
        requires_review, review_reason = self._tag_for_human_review(
            transcript, context, satisfaction
        )

        return CallSummary(
            outcome=outcome,
            satisfaction=satisfaction,
            summary_text=summary_text,
            key_points=key_points,
            next_steps=next_steps,
            requires_human_review=requires_review,
            human_review_reason=review_reason,
        )

    async def _classify_outcome(
        self,
        transcript: List[Dict[str, str]],
        agent: Optional[Agent],
    ) -> CallOutcome:
        """Classify call outcome using LLM or fallback heuristic."""
        if not self.llm or not agent:
            return CallOutcome(
                label=self._heuristic_outcome(transcript),
                confidence=0.6,
                reason="heuristic classification",
            )

        agent_text = "\n".join(
            f"{m.get('role', 'unknown')}: {m.get('content', '')}"
            for m in transcript[-20:]
        )
        goals = agent.success_criteria or []
        failures = agent.failure_conditions or []

        prompt = f"""Analyze this call transcript and classify the outcome.

Success Criteria:
{chr(10).join(f'- {g}' for g in goals)}

Failure Conditions:
{chr(10).join(f'- {f}' for f in failures)}

Transcript (last 20 exchanges):
{agent_text}

Respond exactly in this format:
OUTCOME: success|failure|neutral|escalated
CONFIDENCE: 0.0-1.0
REASON: Brief reason"""

        try:
            response = await self.llm.generate_response(
                "Classify call outcome.", prompt, []
            )
            lines = response.strip().split("\n")
            label = "neutral"
            confidence = 0.6
            reason = "llm classification"
            for line in lines:
                if line.startswith("OUTCOME:"):
                    label = line.split(":", 1)[1].strip().lower()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = float(line.split(":", 1)[1].strip())
                    except ValueError:
                        pass
                elif line.startswith("REASON:"):
                    reason = line.split(":", 1)[1].strip()
            return CallOutcome(label=label, confidence=confidence, reason=reason)
        except Exception as e:
            logger.warning(f"LLM outcome classification failed: {e}")
            return CallOutcome(label="neutral", confidence=0.5, reason=str(e))

    def _heuristic_outcome(self, transcript: List[Dict[str, str]]) -> str:
        """Fallback keyword-based outcome heuristic."""
        if not transcript:
            return "neutral"
        last_user_msgs = [
            m["content"].lower() for m in transcript[-5:]
            if m.get("role") == "user"
        ]
        combined = " ".join(last_user_msgs)
        if any(w in combined for w in ["thank", "great", "helped", "perfect", "bye"]):
            return "success"
        if any(w in combined for w in ["angry", "frustrated", "complaint", "useless"]):
            return "failure"
        if any(w in combined for w in ["manager", "supervisor", "human"]):
            return "escalated"
        return "neutral"

    def _estimate_satisfaction(
        self,
        transcript: List[Dict[str, str]],
        context: Optional[AgentContext],
    ) -> SatisfactionEstimate:
        """Estimate satisfaction from transcript sentiment and context signals."""
        user_msgs = [m["content"] for m in transcript if m.get("role") == "user"]
        if not user_msgs:
            return SatisfactionEstimate(score=0.5, confidence=0.3)

        sentiment_scores = []
        for msg in user_msgs:
            from app.services.emotion_service import _analyze_sentiment
            sentiment_scores.append(_analyze_sentiment(msg))

        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5

        # Trend — last 3 vs overall
        recent = sentiment_scores[-3:] if len(sentiment_scores) >= 3 else sentiment_scores
        trend = sum(recent) / len(recent) - avg_sentiment if recent else 0.0

        frustration_boost = 0.0
        if context:
            frustration_boost = context.frustration_level * 0.2

        score = max(0.0, min(1.0, avg_sentiment + trend * 0.3 - frustration_boost))
        confidence = min(1.0, 0.3 + len(user_msgs) * 0.05)

        signals = {
            "avg_sentiment": round(avg_sentiment, 2),
            "trend": round(trend, 2),
            "total_user_turns": len(user_msgs),
            "frustration_penalty": round(frustration_boost, 2),
        }

        return SatisfactionEstimate(score=round(score, 2), confidence=round(confidence, 2), signals=signals)

    def _schedule_next_steps(
        self,
        outcome: CallOutcome,
        summary_text: str,
    ) -> List[NextStep]:
        """Schedule follow-up actions based on outcome."""
        steps = []
        if outcome.label == "failure":
            steps.append(NextStep(
                action="escalate",
                description=f"Call failed: {outcome.reason}. Escalate for human review.",
                assigned_to="supervisor",
            ))
        elif outcome.label == "success":
            steps.append(NextStep(
                action="mark_complete",
                description="Goal achieved. Update CRM record.",
            ))
        elif outcome.label == "escalated":
            steps.append(NextStep(
                action="follow_up",
                description="Call was escalated. Ensure human agent follows up.",
                assigned_to="relationship_manager",
            ))
        # Always offer a follow-up after neutral/escalated
        if outcome.label in ("neutral", "escalated"):
            steps.append(NextStep(
                action="callback",
                description="Schedule a follow-up callback within 24 hours.",
            ))
        return steps

    def _tag_for_human_review(
        self,
        transcript: List[Dict[str, str]],
        context: Optional[AgentContext],
        satisfaction: SatisfactionEstimate,
    ) -> tuple:
        """Determine if this call needs human review and why."""
        flags: List[str] = []

        if context:
            if context.frustration_level > 0.7:
                flags.append("high_frustration")
            if context.escalation_needed:
                flags.append("escalation_requested")
            if context.interrupt_count > 3:
                flags.append("frequent_interruptions")

        if satisfaction.score < 0.3:
            flags.append("low_satisfaction")

        combined_text = " ".join(
            m.get("content", "") for m in transcript if m.get("role") == "user"
        ).lower()
        sensitive_keywords = ["lawsuit", "legal", "attorney", "lawyer", "sue",
                             "regulatory", "complaint", "ombudsman"]
        for kw in sensitive_keywords:
            if kw in combined_text:
                flags.append(f"keyword_{kw}")
                break

        if flags:
            return True, f"Human review flagged: {', '.join(flags)}"
        return False, None

    async def save_to_db(
        self,
        session_id: str,
        agent_id: str,
        caller_id: Optional[str],
        summary: CallSummary,
        organization_id: Optional[str] = None,
    ) -> None:
        """Persist end-of-call analysis to the audit log and memory."""
        from app.models.analytics import TraceLog
        from datetime import datetime
        import json

        log = TraceLog(
            session_id=session_id,
            agent_id=agent_id,
            trace_type="end_of_call",
            duration_ms=0,
            metadata={
                "outcome": {
                    "label": summary.outcome.label,
                    "confidence": summary.outcome.confidence,
                    "reason": summary.outcome.reason,
                },
                "satisfaction": {
                    "score": summary.satisfaction.score,
                    "confidence": summary.satisfaction.confidence,
                    "signals": summary.satisfaction.signals,
                },
                "summary": summary.summary_text,
                "key_points": summary.key_points,
                "next_steps": [{"action": s.action, "description": s.description} for s in summary.next_steps],
                "requires_human_review": summary.requires_human_review,
                "human_review_reason": summary.human_review_reason,
            },
            caller_id=caller_id,
            organization_id=organization_id,
        )
        self.db.add(log)
        self.db.commit()
        logger.info(f"End-of-call analysis saved for session {session_id}")
