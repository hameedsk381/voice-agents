"""
Tuner integration — external observability, simulation, and testing for voice agents.

Sends lifecycle events (call start, end, transcript, node execution, errors) to a
configured webhook URL so external tools can monitor, test, and analyze agent behavior.
"""
from typing import Any, Dict, Optional

import aiohttp
from loguru import logger

from app.core.config import settings


class TunerService:
    def __init__(self) -> None:
        self.webhook_url: Optional[str] = None
        self._configured = False

    def configure(self, webhook_url: Optional[str] = None) -> None:
        self.webhook_url = webhook_url or (settings.TUNER_WEBHOOK_URL if settings else None)
        self._configured = True

    @property
    def enabled(self) -> bool:
        if not self._configured:
            self.configure()
        return bool(self.webhook_url)

    async def dispatch(
        self,
        event: str,
        payload: Dict[str, Any],
    ) -> None:
        """Send a lifecycle event to the Tuner webhook."""
        if not self.enabled:
            return
        body: Dict[str, Any] = {
            "event": event,
            "payload": payload,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,  # type: ignore[arg-type]
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status >= 400:
                        logger.warning(f"Tuner webhook returned {resp.status} for event {event}")
        except Exception as exc:
            logger.warning(f"Tuner webhook dispatch failed for event {event}: {exc}")

    async def on_call_start(
        self,
        call_id: str,
        agent_id: str,
        to_number: str,
        from_number: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        await self.dispatch("call.started", {
            "call_id": call_id,
            "agent_id": agent_id,
            "to": to_number,
            "from": from_number,
            "metadata": metadata or {},
        })

    async def on_call_end(
        self,
        call_id: str,
        agent_id: str,
        duration_seconds: int,
        outcome: Optional[str] = None,
        transcript: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> None:
        await self.dispatch("call.ended", {
            "call_id": call_id,
            "agent_id": agent_id,
            "duration_seconds": duration_seconds,
            "outcome": outcome,
            "transcript": transcript,
            "summary": summary,
        })

    async def on_turn(
        self,
        call_id: str,
        turn_index: int,
        user_text: str,
        agent_text: str,
        latency_ms: int,
    ) -> None:
        await self.dispatch("call.turn", {
            "call_id": call_id,
            "turn_index": turn_index,
            "user_text": user_text,
            "agent_text": agent_text,
            "latency_ms": latency_ms,
        })

    async def on_node_execute(
        self,
        instance_id: str,
        node_id: str,
        node_type: str,
        status: str,
        context_snapshot: Optional[Dict[str, Any]] = None,
    ) -> None:
        await self.dispatch("workflow.node_executed", {
            "instance_id": instance_id,
            "node_id": node_id,
            "node_type": node_type,
            "status": status,
            "context_snapshot": context_snapshot,
        })

    async def on_workflow_complete(
        self,
        instance_id: str,
        workflow_id: str,
        status: str,
        duration_seconds: int,
        outcome: Optional[str] = None,
    ) -> None:
        await self.dispatch("workflow.completed", {
            "instance_id": instance_id,
            "workflow_id": workflow_id,
            "status": status,
            "duration_seconds": duration_seconds,
            "outcome": outcome,
        })


tuner = TunerService()
