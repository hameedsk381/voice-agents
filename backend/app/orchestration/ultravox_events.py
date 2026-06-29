"""
Shared handling for the Ultravox realtime event stream.

Both the Twilio data-connection handler (telephony.py) and the browser proxy
(websocket_proxy.py) consume the same Ultravox event protocol — transcripts,
tool invocations, and per-turn compliance auditing. This module is the single
source of truth for that logic; the two transports only differ in how they
forward audio / tool results to their respective clients.
"""

from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from app.orchestration.session_manager import session_manager
from app.orchestration.tool_executor import execute_tool
from app.services.monitoring_service import monitoring_service
from app.services.compliance_service import (
    compliance_validator,
    redactor,
    get_baseline_rules,
)
from app.models.compliance import AuditLog


async def run_ultravox_compliance_audit(
    session_id: str,
    agent_id: str,
    organization_id: Optional[str],
    turn_index: int,
    user_input: str,
    ai_response: str,
    state_name: str = "ULTRAVOX_RUNTIME",
) -> None:
    """Thread-safe, loop-safe per-turn compliance auditor for Ultravox sessions.

    Uses its own short-lived DB session so it never shares the request/websocket
    session across threads.
    """
    if not user_input or not ai_response:
        return

    from app.core.database import SessionLocal
    from fastapi.concurrency import run_in_threadpool

    def fetch_rules():
        with SessionLocal() as local_db:
            return get_baseline_rules(db=local_db, organization_id=organization_id)

    rules = await run_in_threadpool(fetch_rules)
    audit_result = await compliance_validator.validate_turn(
        user_input, ai_response, rules, turn_index
    )

    def save_audit():
        with SessionLocal() as local_db:
            audit_log = AuditLog(
                session_id=session_id,
                turn_index=turn_index,
                user_message=redactor.redact_text(user_input),
                ai_response=redactor.redact_text(ai_response),
                is_compliant=audit_result.is_compliant,
                violations=[v.dict() for v in audit_result.violations],
                risk_score=audit_result.risk_score,
                agent_id=agent_id,
                organization_id=organization_id,
                state_name=state_name,
            )
            local_db.add(audit_log)
            local_db.commit()

    await run_in_threadpool(save_audit)

    if not audit_result.is_compliant:
        await monitoring_service.broadcast_event(
            session_id,
            "compliance_alert",
            {
                "severity": "critical",
                "risk_score": audit_result.risk_score,
                "violations": [v.rule_name for v in audit_result.violations],
            },
        )


class UltravoxTranscriptTracker:
    """Buffers Ultravox transcript deltas, finalizes turns, and pairs each
    agent reply with the preceding user turn for compliance auditing.

    Shared by both transports; callers handle transport-specific forwarding
    (e.g. streaming agent text chunks to a browser client) using the returned
    delta/final_text.
    """

    def __init__(
        self,
        agent_id: Optional[str],
        organization_id: Optional[str],
        *,
        state_name: str,
    ):
        self.agent_id = agent_id
        self.organization_id = organization_id
        self.state_name = state_name
        self.buffers: Dict[tuple, str] = {}
        self.unanswered_user_turns: List[str] = []
        self.turn_count = 0

    async def handle(self, event: Dict[str, Any], session_id: Optional[str]) -> Dict[str, Any]:
        """Process one `transcript` event.

        Returns {role, is_final, delta, full_text, final_text}. `final_text` is
        the finalized utterance (non-empty) only on the final delta, else None.
        Side effects on finalization: append to history, broadcast transcription,
        and run the per-turn compliance audit for agent replies.
        """
        role = event.get("role", "agent")
        ordinal = int(event.get("ordinal") or 0)
        key = (role, ordinal)

        delta = event.get("delta") or ""
        full_text = event.get("text")
        is_final = bool(event.get("final"))

        if full_text is not None:
            self.buffers[key] = full_text
        elif delta:
            self.buffers[key] = self.buffers.get(key, "") + delta

        final_text: Optional[str] = None
        if is_final and session_id:
            final_text = self.buffers.pop(key, full_text or delta).strip()
            if final_text:
                mapped_role = "assistant" if role == "agent" else "user"
                await session_manager.add_to_history(session_id, mapped_role, final_text)
                await monitoring_service.broadcast_event(
                    session_id, "transcription", {"text": final_text, "role": mapped_role}
                )

                if mapped_role == "user":
                    self.unanswered_user_turns.append(final_text)
                elif self.unanswered_user_turns and self.agent_id:
                    user_turn = self.unanswered_user_turns.pop(0)
                    self.turn_count += 1
                    try:
                        await run_ultravox_compliance_audit(
                            session_id=session_id,
                            agent_id=self.agent_id,
                            organization_id=self.organization_id,
                            turn_index=self.turn_count,
                            user_input=user_turn,
                            ai_response=final_text,
                            state_name=self.state_name,
                        )
                    except Exception as audit_error:
                        logger.error(f"Ultravox compliance audit failed: {audit_error}")

        return {
            "role": role,
            "is_final": is_final,
            "delta": delta,
            "full_text": full_text,
            "final_text": final_text,
        }


def parse_tool_invocation(event: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """Extract (tool_name, invocation_id, arguments) from an Ultravox tool event."""
    tool_name = event.get("toolName") or event.get("name")
    invocation_id = event.get("invocationId") or event.get("id")
    arguments = event.get("parameters") or event.get("toolCallArguments") or {}
    if not isinstance(arguments, dict):
        arguments = {}
    return tool_name, invocation_id, arguments


async def run_ultravox_tool(
    *,
    tool_name: str,
    arguments: Dict[str, Any],
    invocation_id: str,
    db,
    agent_id: str,
    session_id: Optional[str],
    result_message_type: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Execute a tool and build the Ultravox tool-result payload.

    Returns (result_payload, result_meta). Never raises — execution errors are
    encoded into the payload and meta. The caller is responsible for sending
    `result_payload` over its transport and for any monitoring broadcasts.
    """
    try:
        result_dict = await execute_tool(
            tool_name=tool_name,
            arguments=arguments,
            db=db,
            agent_id=agent_id,
            session_id=session_id,
        )
        result_text = result_dict.get("result", "")
        confidence = result_dict.get("confidence", 1.0)
        metadata = result_dict.get("metadata", {})
        is_error = result_dict.get("error", False)

        payload: Dict[str, Any] = {
            "type": result_message_type,
            "invocationId": invocation_id,
            "result": result_text,
            "responseType": "tool-response",
        }
        if is_error:
            payload["errorType"] = "implementation-error"
            payload["errorMessage"] = result_text

        meta = {
            "name": tool_name,
            "arguments": arguments,
            "result": result_text,
            "confidence": confidence,
            "metadata": metadata,
            "error": is_error,
        }
        return payload, meta
    except Exception as exc:
        logger.error(f"Ultravox tool execution failed ({tool_name}): {exc}")
        payload = {
            "type": result_message_type,
            "invocationId": invocation_id,
            "responseType": "tool-response",
            "errorType": "implementation-error",
            "errorMessage": str(exc),
        }
        meta = {
            "name": tool_name,
            "arguments": arguments,
            "result": str(exc),
            "error": True,
        }
        return payload, meta
