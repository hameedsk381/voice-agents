"""
Map telephony / analytics outcomes to workflow context `last_call_outcome`.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def map_call_to_workflow_outcome(
    *,
    analytics_outcome: Optional[str] = None,
    end_reason: Optional[str] = None,
    short_summary: Optional[str] = None,
) -> str:
    """
    Normalize call end signals into values used by workflow condition nodes.
    """
    end = (end_reason or "").lower()
    summary = (short_summary or "").lower()
    outcome = (analytics_outcome or "").upper()

    if outcome == "SUCCESS":
        if any(k in summary for k in ("promise", "payment", "pay", "commit")):
            return "promise_to_pay"
        return "success"

    if "busy" in end:
        return "busy"
    if any(k in end for k in ("no-answer", "no_answer", "unanswered", "machine")):
        return "no_answer"
    if any(k in end for k in ("hangup", "completed", "ended")):
        if outcome == "FAILURE":
            return "no_answer"
        return "answered"

    if outcome == "FAILURE":
        return "failed"

    return "no_answer"


def build_call_end_event(
    *,
    analytics_outcome: Optional[str] = None,
    end_reason: Optional[str] = None,
    short_summary: Optional[str] = None,
    session_id: Optional[str] = None,
    call_id: Optional[str] = None,
) -> Dict[str, Any]:
    last = map_call_to_workflow_outcome(
        analytics_outcome=analytics_outcome,
        end_reason=end_reason,
        short_summary=short_summary,
    )
    event: Dict[str, Any] = {
        "last_call_outcome": last,
        "call_end_reason": end_reason,
        "call_analytics_outcome": analytics_outcome,
    }
    if session_id:
        event["last_session_id"] = session_id
    if call_id:
        event["last_call_id"] = call_id
    if short_summary:
        event["last_call_summary"] = short_summary
    return event
