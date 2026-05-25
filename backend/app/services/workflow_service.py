"""
Workflow CRUD and instance execution.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.workflow import Workflow, WorkflowInstance, WorkflowInstanceStatus, WorkflowStatus
from app.workflows.engine import WorkflowEngine
from app.workflows.templates import BUILTIN_TEMPLATES, TEMPLATE_BY_SLUG
from app.workflows.sap_ingest import rows_from_csv_dicts
from app.workflows.call_outcome import build_call_end_event
from app.models.campaign import CampaignContact, ContactStatus


class WorkflowService:
    def __init__(self, db: Session):
        self.db = db
        self.engine = WorkflowEngine(db)

    def list_templates(self) -> List[Dict[str, Any]]:
        return [
            {
                "slug": slug,
                "name": tpl.get("name"),
                "description": tpl.get("description"),
                "category": tpl.get("category"),
                "node_count": len(tpl.get("nodes") or []),
            }
            for slug, tpl in TEMPLATE_BY_SLUG.items()
        ]

    def get_template_definition(self, slug: str) -> Optional[Dict[str, Any]]:
        return TEMPLATE_BY_SLUG.get(slug)

    def list_workflows(self, organization_id: Optional[str] = None) -> List[Workflow]:
        q = self.db.query(Workflow).filter(Workflow.is_template == False)  # noqa: E712
        if organization_id:
            q = q.filter(Workflow.organization_id == organization_id)
        return q.order_by(desc(Workflow.updated_at)).all()

    def get_workflow(self, workflow_id: str, organization_id: Optional[str] = None) -> Optional[Workflow]:
        q = self.db.query(Workflow).filter(Workflow.id == workflow_id)
        if organization_id:
            q = q.filter(Workflow.organization_id == organization_id)
        return q.first()

    def create_workflow(
        self,
        *,
        name: str,
        definition: Dict[str, Any],
        description: Optional[str] = None,
        category: Optional[str] = None,
        organization_id: Optional[str] = None,
        created_by: Optional[str] = None,
        status: str = WorkflowStatus.DRAFT.value,
        from_template_slug: Optional[str] = None,
    ) -> Workflow:
        if from_template_slug:
            tpl = self.get_template_definition(from_template_slug)
            if not tpl:
                raise ValueError(f"Unknown template: {from_template_slug}")
            definition = tpl

        self.engine.parse_definition(definition)

        wf = Workflow(
            name=name or definition.get("name") or "Untitled workflow",
            description=description or definition.get("description"),
            category=category or definition.get("category"),
            organization_id=organization_id,
            definition=definition,
            version=definition.get("version", "1"),
            status=status,
            is_template=False,
            template_slug=from_template_slug,
            created_by=created_by,
        )
        self.db.add(wf)
        self.db.commit()
        self.db.refresh(wf)
        return wf

    def update_workflow(
        self,
        workflow_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        definition: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Optional[Workflow]:
        wf = self.get_workflow(workflow_id, organization_id=organization_id)
        if not wf:
            return None
        if definition is not None:
            self.engine.parse_definition(definition)
            wf.definition = definition
            wf.version = definition.get("version", "1")
        if name is not None:
            wf.name = name
        if description is not None:
            wf.description = description
        if status is not None:
            wf.status = status
        wf.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(wf)
        return wf

    def delete_workflow(self, workflow_id: str, organization_id: Optional[str] = None) -> bool:
        wf = self.get_workflow(workflow_id, organization_id=organization_id)
        if not wf:
            return False
        self.db.delete(wf)
        self.db.commit()
        return True

    def publish_workflow(self, workflow_id: str, organization_id: Optional[str] = None) -> Optional[Workflow]:
        return self.update_workflow(workflow_id, status=WorkflowStatus.ACTIVE.value, organization_id=organization_id)

    async def create_instance(
        self,
        workflow_id: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        campaign_id: Optional[str] = None,
        contact_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        auto_start: bool = True,
    ) -> WorkflowInstance:
        wf = self.get_workflow(workflow_id, organization_id=organization_id)
        if not wf:
            raise ValueError("Workflow not found")

        defn = self.engine.parse_definition(wf.definition or {})
        ctx = dict(context or {})
        if campaign_id:
            ctx["campaign_id"] = campaign_id
        if contact_id:
            ctx["contact_id"] = contact_id
        if agent_id:
            ctx["agent_id"] = agent_id
        if organization_id:
            ctx["organization_id"] = organization_id

        inst = WorkflowInstance(
            workflow_id=workflow_id,
            status=WorkflowInstanceStatus.RUNNING.value,
            current_node_id=defn.entry,
            context=ctx,
            campaign_id=campaign_id,
            contact_id=contact_id,
            agent_id=agent_id or ctx.get("agent_id"),
            organization_id=organization_id,
        )
        self.db.add(inst)
        self.db.commit()
        self.db.refresh(inst)

        if auto_start:
            return await self.advance_instance(inst.id)
        return inst

    def get_instance(self, instance_id: str, organization_id: Optional[str] = None) -> Optional[WorkflowInstance]:
        q = self.db.query(WorkflowInstance).filter(WorkflowInstance.id == instance_id)
        if organization_id:
            q = q.filter(WorkflowInstance.organization_id == organization_id)
        return q.first()

    def list_instances(
        self, workflow_id: Optional[str] = None, limit: int = 50, organization_id: Optional[str] = None
    ) -> List[WorkflowInstance]:
        q = self.db.query(WorkflowInstance)
        if workflow_id:
            q = q.filter(WorkflowInstance.workflow_id == workflow_id)
        if organization_id:
            q = q.filter(WorkflowInstance.organization_id == organization_id)
        return q.order_by(desc(WorkflowInstance.created_at)).limit(limit).all()

    async def advance_instance(
        self,
        instance_id: str,
        *,
        event: Optional[Dict[str, Any]] = None,
        organization_id: Optional[str] = None,
    ) -> WorkflowInstance:
        inst = self.get_instance(instance_id, organization_id=organization_id)
        if not inst:
            raise ValueError("Instance not found")

        wf = self.get_workflow(inst.workflow_id, organization_id=inst.organization_id)
        if not wf:
            raise ValueError("Workflow definition missing")

        defn = self.engine.parse_definition(wf.definition or {})
        ctx = dict(inst.context or {})

        if event:
            ctx.update(event)
            if event.get("last_call_outcome"):
                ctx["last_call_outcome"] = event["last_call_outcome"]

        if inst.status == WorkflowInstanceStatus.WAITING.value and inst.wait_until:
            if datetime.utcnow() < inst.wait_until:
                if not event:
                    return inst

        meta = {
            "instance_id": inst.id,
            "campaign_id": inst.campaign_id,
            "contact_id": inst.contact_id,
            "agent_id": inst.agent_id,
        }

        result = await self.engine.run_until_wait_or_done(
            defn,
            current_node_id=inst.current_node_id or defn.entry,
            context=ctx,
            instance_meta=meta,
        )

        inst.context = result.get("context") or ctx
        inst.current_node_id = result.get("current_node_id")
        inst.status = result.get("status", WorkflowInstanceStatus.RUNNING.value)
        inst.wait_until = None
        if result.get("wait_until"):
            inst.wait_until = datetime.fromisoformat(result["wait_until"].replace("Z", ""))
            inst.status = WorkflowInstanceStatus.WAITING.value

        if inst.status == WorkflowInstanceStatus.COMPLETED.value:
            inst.outcome = result.get("outcome") or ctx.get("workflow_outcome")
            inst.completed_at = datetime.utcnow()
        if result.get("error"):
            inst.error_message = result["error"]
            if inst.status not in (WorkflowInstanceStatus.WAITING.value, WorkflowInstanceStatus.COMPLETED.value):
                inst.status = WorkflowInstanceStatus.FAILED.value

        inst.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(inst)
        return inst

    async def process_due_instances(self, limit: int = 100, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Resume workflow instances whose wait_until has passed (cron / Temporal activity)."""
        now = datetime.utcnow()
        q = self.db.query(WorkflowInstance).filter(
            WorkflowInstance.status == WorkflowInstanceStatus.WAITING.value,
            WorkflowInstance.wait_until.isnot(None),
            WorkflowInstance.wait_until <= now,
        )
        if organization_id:
            q = q.filter(WorkflowInstance.organization_id == organization_id)
        due = q.limit(limit).all()
        processed = 0
        errors = 0
        for inst in due:
            try:
                await self.advance_instance(inst.id, event={})
                processed += 1
            except Exception:
                errors += 1
        return {"processed": processed, "errors": errors, "checked": len(due)}

    def list_instances_for_contact(self, contact_id: str, organization_id: Optional[str] = None) -> List[WorkflowInstance]:
        q = self.db.query(WorkflowInstance).filter(WorkflowInstance.contact_id == contact_id)
        if organization_id:
            q = q.filter(WorkflowInstance.organization_id == organization_id)
        return q.order_by(desc(WorkflowInstance.updated_at)).all()

    def list_instances_for_campaign(self, campaign_id: str, organization_id: Optional[str] = None) -> List[WorkflowInstance]:
        q = self.db.query(WorkflowInstance).filter(WorkflowInstance.campaign_id == campaign_id)
        if organization_id:
            q = q.filter(WorkflowInstance.organization_id == organization_id)
        return q.order_by(desc(WorkflowInstance.updated_at)).all()

    async def advance_instances_for_contact(
        self,
        contact_id: str,
        event: Dict[str, Any],
        *,
        active_only: bool = True,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Advance all workflow instances linked to a campaign contact."""
        q = self.db.query(WorkflowInstance).filter(WorkflowInstance.contact_id == contact_id)
        if active_only:
            q = q.filter(
                WorkflowInstance.status.in_(
                    [
                        WorkflowInstanceStatus.RUNNING.value,
                        WorkflowInstanceStatus.WAITING.value,
                    ]
                )
            )
        if organization_id:
            q = q.filter(WorkflowInstance.organization_id == organization_id)
        instances = q.all()
        advanced = 0
        results: List[Dict[str, Any]] = []
        for inst in instances:
            try:
                updated = await self.advance_instance(inst.id, event=event)
                advanced += 1
                results.append(
                    {
                        "instance_id": updated.id,
                        "status": updated.status,
                        "current_node_id": updated.current_node_id,
                        "outcome": updated.outcome,
                    }
                )
            except Exception as exc:
                results.append({"instance_id": inst.id, "error": str(exc)})
        return {"advanced": advanced, "checked": len(instances), "instances": results}

    async def advance_on_call_ended(
        self,
        *,
        contact_id: Optional[str],
        analytics_outcome: Optional[str] = None,
        end_reason: Optional[str] = None,
        short_summary: Optional[str] = None,
        session_id: Optional[str] = None,
        call_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not contact_id:
            return {"advanced": 0, "skipped": True, "reason": "no_contact_id"}
        event = build_call_end_event(
            analytics_outcome=analytics_outcome,
            end_reason=end_reason,
            short_summary=short_summary,
            session_id=session_id,
            call_id=call_id,
        )
        return await self.advance_instances_for_contact(contact_id, event, organization_id=organization_id)

    async def advance_on_hitl_decision(
        self,
        pending_action_id: str,
        *,
        approved: bool,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Resume workflow instances waiting on a HITL approval."""
        q = self.db.query(WorkflowInstance).filter(
            WorkflowInstance.status == WorkflowInstanceStatus.WAITING.value,
        )
        if organization_id:
            q = q.filter(WorkflowInstance.organization_id == organization_id)
        instances = q.all()
        matched = [
            inst
            for inst in instances
            if (inst.context or {}).get("pending_approval_id") == pending_action_id
        ]
        if not approved:
            return {"advanced": 0, "checked": len(matched), "rejected": True}

        advanced = 0
        for inst in matched:
            await self.advance_instance(
                inst.id,
                event={"hitl_approved": True, "last_call_outcome": "approved"},
            )
            advanced += 1
        return {"advanced": advanced, "checked": len(matched)}

    def campaign_workflow_summary(self, campaign_id: str, workflow_id: Optional[str], organization_id: Optional[str] = None) -> Dict[str, Any]:
        wf = self.get_workflow(workflow_id, organization_id=organization_id) if workflow_id else None
        instances = self.list_instances_for_campaign(campaign_id, organization_id=organization_id)
        by_status: Dict[str, int] = {}
        for inst in instances:
            by_status[inst.status] = by_status.get(inst.status, 0) + 1
        return {
            "workflow_id": workflow_id,
            "workflow_name": wf.name if wf else None,
            "workflow_status": wf.status if wf else None,
            "instance_count": len(instances),
            "instances_by_status": by_status,
        }

    async def ingest_sap_rows(
        self,
        workflow_id: str,
        rows: List[Dict[str, Any]],
        *,
        campaign_id: Optional[str] = None,
        create_campaign_name: Optional[str] = None,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        auto_start_instances: bool = True,
    ) -> Dict[str, Any]:
        """Import SAP AR rows, optionally attach to campaign, start workflow per contact."""
        from app.models.campaign import Campaign
        from app.services.campaign_service import CampaignService

        wf = self.get_workflow(workflow_id, organization_id=organization_id)
        if not wf:
            raise ValueError("Workflow not found")
        if wf.status != WorkflowStatus.ACTIVE.value:
            raise ValueError("Workflow must be published (active) before ingest")

        normalized = rows_from_csv_dicts(rows)
        if not normalized:
            raise ValueError("No valid rows with phone/contact_number")

        camp_service = CampaignService(self.db)
        campaign = None
        if campaign_id:
            campaign = await camp_service.get_campaign(campaign_id)
            if not campaign:
                raise ValueError("Campaign not found")
        elif create_campaign_name and agent_id:
            campaign = await camp_service.create_campaign(
                name=create_campaign_name,
                agent_id=agent_id,
                user_id=user_id or "",
                description=f"SAP ingest for workflow {wf.name}",
                workflow_id=workflow_id,
            )
            campaign_id = campaign.id

        contacts_added = 0
        instances_started = 0
        contact_ids: List[str] = []

        for row in normalized:
            phone = row.get("phone_number")
            if not phone:
                continue
            contact_id = None
            if campaign_id:
                added = await camp_service.add_contacts(
                    campaign_id,
                    [
                        {
                            "phone_number": phone,
                            "contact_name": row.get("customer_name"),
                            "custom_data": row,
                        }
                    ],
                )
                contacts_added += added
                contact = (
                    self.db.query(CampaignContact)
                    .filter(
                        CampaignContact.campaign_id == campaign_id,
                        CampaignContact.phone_number == phone,
                    )
                    .order_by(desc(CampaignContact.created_at))
                    .first()
                )
                contact_id = contact.id if contact else None
                if contact_id:
                    contact_ids.append(contact_id)

            if auto_start_instances:
                ctx = dict(row)
                ctx["campaign_id"] = campaign_id
                ctx["contact_id"] = contact_id
                ctx["agent_id"] = agent_id or (campaign.agent_id if campaign else None)
                await self.create_instance(
                    workflow_id,
                    context=ctx,
                    campaign_id=campaign_id,
                    contact_id=contact_id,
                    agent_id=ctx.get("agent_id"),
                    organization_id=organization_id,
                    auto_start=True,
                )
                instances_started += 1

        return {
            "workflow_id": workflow_id,
            "campaign_id": campaign_id,
            "rows_normalized": len(normalized),
            "contacts_added": contacts_added,
            "instances_started": instances_started,
            "contact_ids": contact_ids[:20],
        }

    def seed_builtin_templates(self, created_by: Optional[str] = None) -> int:
        """Idempotently ensure built-in templates exist in DB for cloning."""
        created = 0
        for slug, tpl in TEMPLATE_BY_SLUG.items():
            existing = (
                self.db.query(Workflow)
                .filter(Workflow.template_slug == slug, Workflow.is_template == True)  # noqa: E712
                .first()
            )
            if existing:
                continue
            wf = Workflow(
                name=tpl["name"],
                description=tpl.get("description"),
                category=tpl.get("category"),
                definition=tpl,
                version="1",
                status=WorkflowStatus.ACTIVE.value,
                is_template=True,
                template_slug=slug,
                created_by=created_by,
            )
            self.db.add(wf)
            created += 1
        if created:
            self.db.commit()
        return created
