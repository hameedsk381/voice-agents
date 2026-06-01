"""
In-process workflow executor (v1). Temporal can wrap this later for durability.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import aiohttp
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.hitl import PendingAction
from app.services.tuner_service import tuner as _tuner
from app.workflows.schema import (
    ConditionOperator,
    ConditionRule,
    NodeType,
    StepResult,
    WorkflowDefinitionV1,
    WorkflowNode,
)


def _resolve_template(template: str, context: Dict[str, Any]) -> str:
    """Replace {{var}} placeholders with values from context."""
    def _replacer(m: re.Match) -> str:
        key = m.group(1).strip()
        return str(context.get(key, m.group(0)))
    return re.sub(r"\{\{(\w+)\}\}", _replacer, template)  # type: ignore[arg-type]


def _get_field(context: Dict[str, Any], field: str) -> Any:
    if "." in field:
        cur: Any = context
        for part in field.split("."):
            if not isinstance(cur, dict):
                return None
            cur = cur.get(part)
        return cur
    return context.get(field)


def _eval_rule(context: Dict[str, Any], rule: ConditionRule) -> bool:
    actual = _get_field(context, rule.field)
    expected = rule.value
    op = rule.op

    if op == ConditionOperator.EQ:
        return actual == expected
    if op == ConditionOperator.NEQ:
        return actual != expected
    if op == ConditionOperator.GT:
        return actual is not None and actual > expected
    if op == ConditionOperator.GTE:
        return actual is not None and actual >= expected
    if op == ConditionOperator.LT:
        return actual is not None and actual < expected
    if op == ConditionOperator.LTE:
        return actual is not None and actual <= expected
    if op == ConditionOperator.IN:
        return actual in (expected or [])
    if op == ConditionOperator.CONTAINS:
        return expected in (actual or [])
    return False


def _render_template(template: str, context: Dict[str, Any]) -> str:
    """Replace {{var}} and {{var|default}} placeholders from context."""
    import re
    def _replacer(m: re.Match) -> str:
        key = m.group(1).strip()
        parts = key.split("|", 1)
        val = context.get(parts[0])
        if val is None:
            return parts[1] if len(parts) > 1 else ""
        return str(val)
    return re.sub(r"\{\{([^}]+)\}\}", _replacer, template)


def _eval_condition(node: WorkflowNode, context: Dict[str, Any]) -> bool:
    rules_raw = node.config.get("rules") or []
    match_mode = node.config.get("match", "all")
    if not rules_raw:
        return False
    results = []
    for r in rules_raw:
        rule = ConditionRule(**r) if isinstance(r, dict) else r
        results.append(_eval_rule(context, rule))
    if match_mode == "any":
        return any(results)
    return all(results)


class WorkflowEngine:
    def __init__(self, db: Session):
        self.db = db

    def parse_definition(self, raw: Dict[str, Any]) -> WorkflowDefinitionV1:
        defn = WorkflowDefinitionV1.model_validate(raw)
        defn.validate_graph()
        return defn

    async def execute_node(
        self,
        node: WorkflowNode,
        context: Dict[str, Any],
        instance_meta: Dict[str, Any],
    ) -> StepResult:
        if node.type == NodeType.START:
            return StepResult(status="continue", next_node_id=node.next)

        if node.type == NodeType.CONDITION:
            passed = _eval_condition(node, context)
            nxt = node.on_true if passed else node.on_false
            return StepResult(
                status="continue",
                next_node_id=nxt,
                message=f"condition={'true' if passed else 'false'}",
                context_patch={"last_condition": passed},
            )

        if node.type == NodeType.VOICE_CALL:
            attempts = int(context.get("call_attempts") or 0) + 1
            max_attempts = int(node.config.get("max_attempts") or 3)
            patch = {
                "call_attempts": attempts,
                "last_step": "voice_call",
                "last_call_status": "queued",
            }

            data_fetch_url = node.config.get("data_fetch_url", "")
            if data_fetch_url:
                try:
                    resolved_url = _resolve_template(data_fetch_url, {**instance_meta, **context})
                    method = node.config.get("data_fetch_method", "GET").upper()
                    headers = node.config.get("data_fetch_headers", {})
                    response_key = node.config.get("data_fetch_response_key", "precall_data")
                    async with aiohttp.ClientSession() as session:
                        if method == "POST":
                            body_template = node.config.get("data_fetch_body", "")
                            body = _resolve_template(body_template, {**instance_meta, **context}) if body_template else None
                            async with session.post(resolved_url, headers=headers, json=json.loads(body) if body else None) as resp:
                                data = await resp.json()
                        else:
                            async with session.get(resolved_url, headers=headers) as resp:
                                data = await resp.json()
                    patch[response_key] = data
                    logger.info(f"Pre-call data fetch from {resolved_url}: OK")
                except Exception as exc:
                    logger.warning(f"Pre-call data fetch failed: {exc}")
                    patch["precall_fetch_error"] = str(exc)

            campaign_id = context.get("campaign_id") or instance_meta.get("campaign_id")
            contact_id = context.get("contact_id") or instance_meta.get("contact_id")
            if campaign_id and contact_id:
                try:
                    from app.services.campaign_service import CampaignService

                    service = CampaignService(self.db)
                    result = await service.dial_contact(str(campaign_id), str(contact_id))
                    patch["last_call_status"] = "dialed"
                    patch["last_session_id"] = result.get("session_id")
                except Exception as exc:
                    logger.warning(f"Workflow voice_call dial failed: {exc}")
                    patch["last_call_status"] = "dial_failed"
                    patch["last_call_error"] = str(exc)
                    patch["last_call_outcome"] = "failed"
            else:
                patch["last_call_status"] = "planned"
                patch["last_call_outcome"] = context.get("last_call_outcome") or "pending"

            if patch.get("last_call_outcome") in (None, "pending", "planned"):
                return StepResult(
                    status="waiting",
                    next_node_id=node.next,
                    message="Awaiting call outcome",
                    context_patch=patch,
                )
            if attempts < max_attempts and patch.get("last_call_outcome") in (
                "no_answer",
                "busy",
                "failed",
                "no_pickup",
            ):
                delays = node.config.get("retry_delay_minutes") or [60]
                delay_min = delays[min(attempts - 1, len(delays) - 1)]
                wait_until = (datetime.utcnow() + timedelta(minutes=int(delay_min))).isoformat()
                return StepResult(
                    status="waiting",
                    next_node_id=node.id,
                    message=f"Retry call in {delay_min} minutes",
                    context_patch=patch,
                    wait_until=wait_until,
                )
            return StepResult(
                status="continue",
                next_node_id=node.next,
                message="Voice call step complete",
                context_patch=patch,
            )

        if node.type == NodeType.RECORDED_AUDIO:
            audio_url = node.config.get("audio_url", "")
            audio_file = node.config.get("audio_file", "")
            if not audio_url and not audio_file:
                return StepResult(
                    status="failed",
                    message="No audio_url or audio_file configured",
                    context_patch={"recorded_audio_error": "missing source"},
                )
            return StepResult(
                status="continue",
                next_node_id=node.next,
                message=f"Play pre-recorded audio: {audio_url or audio_file}",
                context_patch={
                    "recorded_audio_url": audio_url,
                    "recorded_audio_file": audio_file,
                    "last_step": "recorded_audio",
                },
            )

        if node.type == NodeType.WAIT:
            minutes = int(node.config.get("minutes") or 60)
            wait_until = (datetime.utcnow() + timedelta(minutes=minutes)).isoformat()
            return StepResult(
                status="waiting",
                next_node_id=node.next,
                message=f"Waiting {minutes} minutes",
                wait_until=wait_until,
            )

        if node.type == NodeType.EMAIL:
            from app.services.email_service import EmailService

            to_addr = (
                context.get("email")
                or context.get("contact_email")
                or instance_meta.get("email")
            )
            template = node.config.get("template") or "payment_reminder"
            email_status = "skipped"
            if to_addr:
                svc = EmailService(self.db)
                row = await svc.send_template_email(
                    to_address=str(to_addr),
                    template=template,
                    context=context,
                    workflow_instance_id=instance_meta.get("instance_id"),
                )
                email_status = row.status
            return StepResult(
                status="continue",
                next_node_id=node.next,
                message=f"Email {email_status} ({template})",
                context_patch={
                    "last_email_template": template,
                    "last_email_status": email_status,
                    "emails_sent": int(context.get("emails_sent") or 0) + 1,
                },
            )

        if node.type == NodeType.WHATSAPP:
            phone = (
                context.get("phone_number")
                or context.get("contact_number")
                or instance_meta.get("phone_number")
            )
            template = node.config.get("template") or "payment_reminder"
            wa_status = "skipped"
            if phone:
                from app.services.whatsapp_service import WhatsAppService, render_template

                message_body = node.config.get("message")
                if not message_body:
                    message_body = render_template(template, context)

                wa_service = WhatsAppService(db=self.db)
                result = wa_service.send_message(
                    str(phone),
                    message_body,
                    workflow_instance_id=instance_meta.get("instance_id"),
                    template_name=template,
                    organization_id=context.get("organization_id"),
                )
                wa_status = result.get("status", "failed")

                logger.info(
                    f"[whatsapp] to={phone} template={template} "
                    f"status={wa_status} instance={instance_meta.get('instance_id')}"
                )
            return StepResult(
                status="continue",
                next_node_id=node.next,
                message=f"WhatsApp {wa_status} ({template})",
                context_patch={
                    "last_whatsapp_template": template,
                    "last_whatsapp_status": wa_status,
                    "last_whatsapp_message": context.get("message", ""),
                    "whatsapp_sent": int(context.get("whatsapp_sent") or 0) + 1,
                },
            )

        if node.type == NodeType.HITL_APPROVAL:
            agent_id = context.get("agent_id") or instance_meta.get("agent_id")
            session_id = context.get("last_session_id") or instance_meta.get("instance_id", "workflow")
            action = PendingAction(
                session_id=str(session_id),
                agent_id=str(agent_id) if agent_id else None,
                organization_id=context.get("organization_id"),
                action_type=node.config.get("action_type") or "workflow_approval",
                description=node.config.get("description") or f"Approval required at {node.id}",
                payload={
                    "workflow_node": node.id,
                    "context_snapshot": {
                        k: context.get(k)
                        for k in (
                            "customer_name",
                            "customer_id",
                            "outstanding_amount",
                            "aging_bucket",
                            "branch_code",
                        )
                        if context.get(k) is not None
                    },
                },
                status="pending",
            )
            self.db.add(action)
            self.db.commit()
            return StepResult(
                status="waiting",
                next_node_id=node.next,
                message="Awaiting human approval",
                context_patch={"pending_approval_id": action.id},
            )

        if node.type == NodeType.AGENT_TASK:
            target_agent_id = node.config.get("agent_id") or context.get("routed_agent_id")
            capability = node.config.get("capability") or ""
            task_input = node.config.get("input") or context.get("agent_task_input", "")

            if not target_agent_id and capability:
                from app.services.agent_registry_service import AgentRegistryService
                registry = AgentRegistryService(self.db)
                found = registry.find_agent_for_capability(capability)
                if found:
                    target_agent_id = found.id

            if not target_agent_id:
                return StepResult(
                    status="failed",
                    message=f"No target agent for agent_task node '{node.id}'",
                    context_patch={"agent_task_error": "no_target_agent"},
                )

            from app.orchestration.agent_swarm import SwarmOrchestrator
            from app.models.agent import Agent
            target_agent = self.db.query(Agent).filter(Agent.id == target_agent_id).first()
            if not target_agent:
                return StepResult(
                    status="failed",
                    message=f"Target agent {target_agent_id} not found",
                    context_patch={"agent_task_error": "agent_not_found"},
                )

            swarm = SwarmOrchestrator(self.db, target_agent)
            task_result = await swarm.route_task(task_input, [], [target_agent])
            agent_name = task_result.name if hasattr(task_result, 'name') else target_agent.name

            return StepResult(
                status="continue",
                next_node_id=node.next,
                message=f"Routed to agent '{agent_name}' for capability '{capability}'",
                context_patch={
                    "routed_agent_id": target_agent_id,
                    "routed_agent_name": agent_name,
                    "last_agent_task": capability,
                },
            )

        if node.type == NodeType.ESCALATE:
            owner = node.config.get("owner_role") or "account_owner"
            return StepResult(
                status="continue",
                next_node_id=node.next,
                message=f"Escalated to {owner}",
                context_patch={
                    "escalated_to": owner,
                    "escalation_priority": node.config.get("priority"),
                    "escalation_count": int(context.get("escalation_count") or 0) + 1,
                },
            )

        if node.type == NodeType.END:
            return StepResult(
                status="completed",
                message=node.config.get("outcome") or "completed",
                context_patch={"workflow_outcome": node.config.get("outcome") or "completed"},
            )

        if node.type == NodeType.SMS:
            phone = (
                node.config.get("to_phone")
                or context.get("phone_number")
                or context.get("contact_number")
                or instance_meta.get("phone_number")
            )
            raw_message = node.config.get("message") or "Notification from Voise AI"
            message = _render_template(raw_message, context)
            sms_status = "skipped"
            if phone:
                try:
                    from app.core.config import settings
                    from twilio.rest import Client

                    account_sid = settings.TWILIO_ACCOUNT_SID
                    auth_token = settings.TWILIO_AUTH_TOKEN
                    from_number = settings.TWILIO_PHONE_NUMBER
                    if account_sid and auth_token and from_number:
                        client = Client(account_sid, auth_token)
                        twilio_msg = client.messages.create(
                            body=message,
                            from_=from_number,
                            to=str(phone),
                        )
                        sms_status = "sent"
                        sid = twilio_msg.sid
                    else:
                        sms_status = "simulated"
                        sid = None
                        logger.info(f"[workflow sms] simulated to={phone} msg={message[:60]}")
                except Exception as exc:
                    sms_status = "failed"
                    sid = None
                    logger.warning(f"[workflow sms] failed to={phone}: {exc}")

                from app.models.workflow import SmsMessage
                sms_row = SmsMessage(
                    workflow_instance_id=instance_meta.get("instance_id"),
                    organization_id=context.get("organization_id"),
                    to_phone=str(phone),
                    message_body=message,
                    status=sms_status,
                    provider_message_sid=sid,
                )
                self.db.add(sms_row)
                self.db.commit()

            return StepResult(
                status="continue",
                next_node_id=node.next,
                message=f"SMS {sms_status}",
                context_patch={
                    "last_sms_status": sms_status,
                    "sms_sent": int(context.get("sms_sent") or 0) + 1,
                },
            )

        if node.type == NodeType.WEBHOOK:
            import httpx

            url_template = node.config.get("url") or ""
            method = (node.config.get("method") or "POST").upper()
            raw_headers = node.config.get("headers") or {}
            body_template = node.config.get("body_template")
            response_key = node.config.get("response_key") or "webhook_response"

            url = _render_template(url_template, context)
            headers = {
                k: _render_template(str(v), context) for k, v in raw_headers.items()
            }
            body = _render_template(body_template, context) if body_template else None

            webhook_status = "skipped"
            webhook_data = {}
            if url:
                try:
                    async with httpx.AsyncClient(timeout=30.0) as hc:
                        if method == "GET":
                            resp = await hc.get(url, headers=headers)
                        else:
                            content_type = headers.get("Content-Type", "application/json")
                            if content_type == "application/json" and body:
                                import json as _json
                                try:
                                    parsed_body = _json.loads(body)
                                except _json.JSONDecodeError:
                                    parsed_body = body
                                resp = await hc.post(url, json=parsed_body, headers=headers)
                            else:
                                resp = await hc.post(url, content=body, headers=headers)

                    webhook_status = "success" if resp.is_success else f"http_{resp.status_code}"
                    webhook_data = {
                        "status_code": resp.status_code,
                        "body": resp.text[:2000],
                    }
                except Exception as exc:
                    webhook_status = "failed"
                    webhook_data = {"error": str(exc)}
                    logger.warning(f"[workflow webhook] {method} {url}: {exc}")

            return StepResult(
                status="continue",
                next_node_id=node.next,
                message=f"Webhook {webhook_status}",
                context_patch={
                    response_key: webhook_data,
                    "last_webhook_status": webhook_status,
                    "webhooks_called": int(context.get("webhooks_called") or 0) + 1,
                },
            )

        if node.type == NodeType.DB_QUERY:
            query_sql = node.config.get("query") or ""
            result_key = node.config.get("result_key") or "query_result"
            dbq_status = "skipped"
            dbq_result = []
            if query_sql:
                try:
                    params = {}
                    import re as _re
                    for match in _re.finditer(r":(\w+)", query_sql):
                        param_name = match.group(1)
                        if param_name not in params:
                            params[param_name] = context.get(param_name)

                    rows = self.db.execute(text(query_sql), params).fetchall()
                    dbq_result = [dict(r._mapping) for r in rows]
                    dbq_status = f"{len(dbq_result)} rows"
                except Exception as exc:
                    dbq_status = "failed"
                    dbq_result = {"error": str(exc)}
                    logger.warning(f"[workflow db_query] error: {exc}")

            return StepResult(
                status="continue",
                next_node_id=node.next,
                message=f"DB query {dbq_status}",
                context_patch={
                    result_key: dbq_result,
                    "last_db_query_status": dbq_status,
                },
            )

        if node.type == NodeType.FORK:
            branches = node.config.get("branches") or []
            return StepResult(
                status="continue",
                next_node_id=branches[0] if branches else node.next,
                context_patch={
                    "_fork_tracker": {
                        "branches": list(branches),
                        "pending": list(branches),
                        "join_node": node.next,
                    }
                },
                message=f"Fork into {len(branches)} branch(es)",
            )

        if node.type == NodeType.JOIN:
            tracker = context.get("_fork_tracker")
            if tracker and tracker.get("pending"):
                tracker["pending"].pop(0)
                if tracker["pending"]:
                    return StepResult(
                        status="continue",
                        next_node_id=tracker["pending"][0],
                        context_patch={"_fork_tracker": tracker},
                        message="Branch completed, next branch",
                    )
                return StepResult(
                    status="continue",
                    next_node_id=node.next,
                    context_patch={"_fork_tracker": None},
                    message="All branches merged",
                )
            return StepResult(status="continue", next_node_id=node.next)

        return StepResult(status="failed", message=f"Unknown node type: {node.type}")

    async def run_until_wait_or_done(
        self,
        definition: WorkflowDefinitionV1,
        *,
        current_node_id: str,
        context: Dict[str, Any],
        instance_meta: Dict[str, Any],
        max_steps: int = 50,
    ) -> Dict[str, Any]:
        node_map = definition.node_map()
        node_id = current_node_id
        steps = 0
        history = list(context.get("_step_history") or [])

        while node_id and steps < max_steps:
            steps += 1
            node = node_map.get(node_id)
            if not node:
                return {
                    "status": "failed",
                    "current_node_id": node_id,
                    "context": context,
                    "error": f"Unknown node {node_id}",
                }

            if node.type == NodeType.START:
                node_id = node.next or definition.entry
                continue

            result = await self.execute_node(node, context, instance_meta)
            context.update(result.context_patch)
            history.append(
                {
                    "node_id": node.id,
                    "type": node.type.value,
                    "at": datetime.utcnow().isoformat(),
                    "message": result.message,
                    "status": result.status,
                }
            )
            context["_step_history"] = history

            await _tuner.on_node_execute(
                instance_id=instance_meta.get("instance_id", ""),
                node_id=node.id,
                node_type=node.type.value,
                status=result.status,
                context_snapshot={
                    k: v for k, v in context.items()
                    if not k.startswith("_") and isinstance(v, (str, int, float, bool, type(None)))
                },
            )

            if result.status == "completed":
                tracker = context.get("_fork_tracker")
                if tracker and tracker.get("pending"):
                    tracker["pending"].pop(0)
                    if tracker["pending"]:
                        node_id = tracker["pending"][0]
                        context["_fork_tracker"] = tracker
                        continue
                    node_id = tracker["join_node"]
                    context["_fork_tracker"] = None
                    continue
                await _tuner.on_workflow_complete(
                    instance_id=instance_meta.get("instance_id", ""),
                    workflow_id=instance_meta.get("workflow_id", ""),
                    status="completed",
                    duration_seconds=0,
                    outcome=context.get("workflow_outcome"),
                )
                return {
                    "status": "completed",
                    "current_node_id": node.id,
                    "context": context,
                    "outcome": context.get("workflow_outcome"),
                }
            if result.status == "failed":
                await _tuner.on_workflow_complete(
                    instance_id=instance_meta.get("instance_id", ""),
                    workflow_id=instance_meta.get("workflow_id", ""),
                    status="failed",
                    duration_seconds=0,
                    outcome=result.message,
                )
                return {
                    "status": "failed",
                    "current_node_id": node.id,
                    "context": context,
                    "error": result.message,
                }
            if result.status == "waiting":
                return {
                    "status": "waiting",
                    "current_node_id": result.next_node_id or node.next or node.id,
                    "context": context,
                    "wait_until": result.wait_until,
                    "message": result.message,
                }

            node_id = result.next_node_id or node.next

        return {
            "status": "failed",
            "current_node_id": node_id,
            "context": context,
            "error": "Max steps exceeded or dead end",
        }
