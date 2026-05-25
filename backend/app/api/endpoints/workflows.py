"""
Workflow automation API — definitions, templates, instances, and WhatsApp.
"""
from typing import Any, Dict, List, Optional

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core import database
from app.core.deps import get_current_user_required
from app.models.user import User
from app.services.workflow_service import WorkflowService

router = APIRouter()


class WorkflowCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None
    from_template_slug: Optional[str] = None
    status: Optional[str] = "draft"


class WorkflowUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class InstanceStartRequest(BaseModel):
    context: Dict[str, Any] = Field(default_factory=dict)
    campaign_id: Optional[str] = None
    contact_id: Optional[str] = None
    agent_id: Optional[str] = None
    auto_start: bool = True


class InstanceAdvanceRequest(BaseModel):
    last_call_outcome: Optional[str] = None
    event: Optional[Dict[str, Any]] = None


class SapIngestRequest(BaseModel):
    workflow_id: str
    campaign_id: Optional[str] = None
    create_campaign_name: Optional[str] = None
    agent_id: Optional[str] = None
    auto_start_instances: bool = True


def _workflow_dict(wf) -> Dict[str, Any]:
    return {
        "id": wf.id,
        "name": wf.name,
        "description": wf.description,
        "category": wf.category,
        "definition": wf.definition,
        "version": wf.version,
        "status": wf.status,
        "template_slug": wf.template_slug,
        "organization_id": wf.organization_id,
        "created_at": wf.created_at.isoformat() if wf.created_at else None,
        "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
    }


def _instance_dict(inst) -> Dict[str, Any]:
    return {
        "id": inst.id,
        "workflow_id": inst.workflow_id,
        "status": inst.status,
        "current_node_id": inst.current_node_id,
        "context": inst.context,
        "wait_until": inst.wait_until.isoformat() if inst.wait_until else None,
        "campaign_id": inst.campaign_id,
        "contact_id": inst.contact_id,
        "agent_id": inst.agent_id,
        "organization_id": inst.organization_id,
        "outcome": inst.outcome,
        "error_message": inst.error_message,
        "created_at": inst.created_at.isoformat() if inst.created_at else None,
        "updated_at": inst.updated_at.isoformat() if inst.updated_at else None,
        "completed_at": inst.completed_at.isoformat() if inst.completed_at else None,
    }


@router.get("/templates")
async def list_templates(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = WorkflowService(db)
    service.seed_builtin_templates(created_by=current_user.id)
    return {"templates": service.list_templates()}


@router.get("/templates/{slug}")
async def get_template(
    slug: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = WorkflowService(db)
    tpl = service.get_template_definition(slug)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"slug": slug, "definition": tpl}


@router.get("/active")
async def list_active_workflows(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = WorkflowService(db)
    workflows = service.list_workflows(organization_id=current_user.organization_id)
    return [
        {"id": w.id, "name": w.name, "category": w.category}
        for w in workflows
        if w.status == "active"
    ]


@router.post("/process-due")
async def process_due_workflow_instances(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Resume instances past wait_until (call from cron or Temporal worker)."""
    service = WorkflowService(db)
    return await service.process_due_instances(organization_id=current_user.organization_id)


@router.post("/ingest/sap-csv")
async def ingest_sap_csv(
    workflow_id: str,
    file: UploadFile = File(...),
    campaign_id: Optional[str] = None,
    create_campaign_name: Optional[str] = None,
    agent_id: Optional[str] = None,
    auto_start: bool = True,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    content = await file.read()
    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))
    rows = list(reader)
    service = WorkflowService(db)
    try:
        return await service.ingest_sap_rows(
            workflow_id,
            rows,
            campaign_id=campaign_id,
            create_campaign_name=create_campaign_name,
            agent_id=agent_id,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            auto_start_instances=auto_start,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class GenerateFromPromptRequest(BaseModel):
    prompt: str


@router.post("/ai/generate")
async def generate_workflow_from_prompt(
    body: GenerateFromPromptRequest,
    current_user: User = Depends(get_current_user_required),
):
    from app.services.llm.enterprise_llm import EnterpriseLLM

    llm = EnterpriseLLM()

    system_prompt = """You are a workflow automation expert for Indian businesses. Based on the user's request, generate a complete workflow definition as raw JSON. Return ONLY the JSON object — no explanations, no markdown, no code fences, no backticks.

AVAILABLE NODE TYPES:
- condition: Branching. Config: {"rules":[{"field":"...","op":"eq|neq|gt|gte|lt|lte|in|contains","value":...}],"match":"all|any"}. Has on_true / on_false edges.
- voice_call: Outbound call. Config: {"max_attempts":3,"retry_delay_minutes":[240,1440,2880]}. Uses next edge.
- wait: Pause. Config: {"minutes":60}. Uses next edge.
- email: Send email. Config: {"template":"payment_reminder|lead_nurture|appointment_confirm"}. Uses next edge.
- whatsapp: WhatsApp message. Config: {"template":"...","message":"..."}. Uses next edge.
- sms: SMS text message. Config: {"message":"Dear {{customer_name}}, ..."}. Uses next edge.
- webhook: HTTP call to external API. Config: {"url":"https://...","method":"POST","headers":{},"body_template":"...","response_key":"webhook_resp"}. Supports {{var}} templating. Uses next edge.
- db_query: SQL query against internal DB. Config: {"query":"SELECT * FROM...","result_key":"result"}. Parameters via :param_name from context. Uses next edge.
- hitl_approval: Human approval. Config: {"action_type":"...","description":"..."}. Uses next edge.
- escalate: Escalate. Config: {"owner_role":"branch_owner|relationship_manager|legal","priority":"low|medium|high"}. Uses next edge.
- agent_task: Route to another AI agent. Config: {"capability":"...","input":"..."}. Uses next edge.
- fork: Parallel branches. Config: {"branches":["branch1_id","branch2_id"]}. Branches converge at a join node. Uses next edge (join point).
- join: Merge point for fork branches. Uses next edge (continues after all branches complete).
- end: End. Config: {"outcome":"success|escalated|failed|nurture|confirmed|email_sent"}

RULES:
1. Use unique short IDs like "check_vip", "call1", "email1", "end_ok".
2. Entry node ID goes in "entry".
3. Conditions need both on_true and on_false.
4. Use Indian business fields: aging_days, outstanding_amount, branch_code, vip_no_auto_call, last_call_outcome, call_attempts.
5. Escalate to "branch_owner", "relationship_manager", or "legal".
6. For parallel execution: fork node's "branches" lists start nodes, join node is where all branches converge.

OUTPUT — raw JSON only:
{"version":"1","name":"...","description":"...","category":"collections|sales|healthcare|custom","entry":"id1","nodes":[{"id":"id1","type":"condition",...}]}"""

    prompt = f"""Request: {body.prompt}

Generate a complete workflow definition as raw JSON for this request. Think step by step then output ONLY the JSON object."""

    response = await llm.generate_response(prompt, system_prompt, [])

    import json
    import re

    text = response.strip()

    json_str = None
    for delim in ['```json', '```', '``']:
        if delim in text:
            parts = text.split(delim)
            if len(parts) >= 2:
                candidate = parts[1].split('```')[0].strip()
                if candidate.startswith('{'):
                    json_str = candidate
                    break

    if not json_str:
        brace_match = re.search(r'(\{.*\})', text, re.DOTALL)
        if brace_match:
            json_str = brace_match.group(1)

    if not json_str:
        raise HTTPException(status_code=422, detail=f"AI did not return valid JSON. Response: {text[:500]}")

    try:
        definition = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"AI generated malformed JSON: {e}. Raw: {json_str[:500]}")
    
    return {"definition": definition}


@router.get("")
async def list_workflows(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = WorkflowService(db)
    workflows = service.list_workflows(organization_id=current_user.organization_id)
    return [_workflow_dict(w) for w in workflows]


@router.post("")
async def create_workflow(
    body: WorkflowCreateRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = WorkflowService(db)
    try:
        wf = service.create_workflow(
            name=body.name,
            definition=body.definition or {},
            description=body.description,
            category=body.category,
            created_by=current_user.id,
            organization_id=current_user.organization_id,
            status=body.status or "draft",
            from_template_slug=body.from_template_slug,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _workflow_dict(wf)


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, organization_id=current_user.organization_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _workflow_dict(wf)


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    body: WorkflowUpdateRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = WorkflowService(db)
    try:
        wf = service.update_workflow(
            workflow_id,
            name=body.name,
            description=body.description,
            definition=body.definition,
            status=body.status,
            organization_id=current_user.organization_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _workflow_dict(wf)


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = WorkflowService(db)
    if not service.delete_workflow(workflow_id, organization_id=current_user.organization_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"deleted": True}


@router.post("/{workflow_id}/publish")
async def publish_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = WorkflowService(db)
    wf = service.publish_workflow(workflow_id, organization_id=current_user.organization_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _workflow_dict(wf)


@router.get("/{workflow_id}/instances")
async def list_instances(
    workflow_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = WorkflowService(db)
    instances = service.list_instances(workflow_id=workflow_id, organization_id=current_user.organization_id)
    return [_instance_dict(i) for i in instances]


@router.post("/{workflow_id}/instances")
async def start_instance(
    workflow_id: str,
    body: InstanceStartRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = WorkflowService(db)
    try:
        inst = await service.create_instance(
            workflow_id,
            context=body.context,
            campaign_id=body.campaign_id,
            contact_id=body.contact_id,
            agent_id=body.agent_id,
            organization_id=current_user.organization_id,
            auto_start=body.auto_start,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _instance_dict(inst)


@router.get("/instances/{instance_id}")
async def get_instance(
    instance_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = WorkflowService(db)
    inst = service.get_instance(instance_id, organization_id=current_user.organization_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    return _instance_dict(inst)


@router.post("/instances/{instance_id}/advance")
async def advance_instance(
    instance_id: str,
    body: InstanceAdvanceRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    service = WorkflowService(db)
    event = body.event or {}
    if body.last_call_outcome:
        event["last_call_outcome"] = body.last_call_outcome
    try:
        inst = await service.advance_instance(instance_id, event=event or None, organization_id=current_user.organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _instance_dict(inst)


# ==================== WHATSAPP ====================


class WhatsAppSendRequest(BaseModel):
    to_phone: str
    message: str
    template: Optional[str] = None
    workflow_instance_id: Optional[str] = None


# ── Send ────────────────────────────────────────────────────────────────


class WhatsAppSendRequest(BaseModel):
    to_phone: str
    message: str
    template: Optional[str] = None
    workflow_instance_id: Optional[str] = None
    media_url: Optional[str] = None


@router.post("/whatsapp/send")
async def send_whatsapp(
    body: WhatsAppSendRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Send a WhatsApp message via Twilio WhatsApp Business API."""
    from app.services.whatsapp_service import WhatsAppService

    service = WhatsAppService(db=db)
    return service.send_message(
        body.to_phone,
        body.message,
        template_name=body.template,
        workflow_instance_id=body.workflow_instance_id,
        organization_id=current_user.organization_id,
        media_url=body.media_url,
    )


class WhatsAppTemplateSendRequest(BaseModel):
    to_phone: str
    template_name: str
    context: Dict[str, Any] = {}
    workflow_instance_id: Optional[str] = None


@router.post("/whatsapp/send-template")
async def send_whatsapp_template(
    body: WhatsAppTemplateSendRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Render and send a built-in WhatsApp template."""
    from app.services.whatsapp_service import WhatsAppService

    service = WhatsAppService(db=db)
    return service.send_template(
        body.to_phone,
        body.template_name,
        body.context,
        workflow_instance_id=body.workflow_instance_id,
        organization_id=current_user.organization_id,
    )


# ── Delivery status ──────────────────────────────────────────────────────


@router.get("/whatsapp/status/{message_sid}")
async def check_whatsapp_delivery(
    message_sid: str,
    current_user: User = Depends(get_current_user_required),
):
    """Check delivery status of a WhatsApp message via Twilio API."""
    from app.services.whatsapp_service import WhatsAppService

    service = WhatsAppService()
    return service.check_delivery_status(message_sid)


# ── Status callback webhook (Twilio → us) ────────────────────────────────


@router.post("/whatsapp/callback")
async def whatsapp_status_callback(
    request: Request,
    db: Session = Depends(database.get_db),
):
    """Twilio status callback webhook for WhatsApp delivery updates."""
    form = await request.form()
    payload = dict(form)
    from app.services.whatsapp_service import WhatsAppService

    service = WhatsAppService(db=db)
    service.handle_status_callback(payload)
    return {"ok": True}


# ── Inbound message webhook (WhatsApp user → Twilio → us) ────────────────


@router.post("/whatsapp/inbound")
async def whatsapp_inbound(
    request: Request,
    db: Session = Depends(database.get_db),
):
    """Inbound WhatsApp message webhook (opt-in, opt-out, replies)."""
    form = await request.form()
    payload = dict(form)
    from app.services.whatsapp_service import WhatsAppService

    service = WhatsAppService(db=db)
    return service.handle_inbound(payload)


# ── Template management ──────────────────────────────────────────────────


class WhatsAppTemplateCreateRequest(BaseModel):
    name: str
    body: str
    language: str = "en"
    category: str = "MARKETING"


@router.post("/whatsapp/templates")
async def create_whatsapp_template(
    body: WhatsAppTemplateCreateRequest,
    current_user: User = Depends(get_current_user_required),
):
    """Create a WhatsApp content template via Twilio Content API."""
    from app.services.whatsapp_service import WhatsAppService

    service = WhatsAppService()
    return service.create_content_template(body.name, body.body, body.language, body.category)


@router.get("/whatsapp/templates")
async def list_whatsapp_templates(
    current_user: User = Depends(get_current_user_required),
):
    """List all WhatsApp content templates from Twilio."""
    from app.services.whatsapp_service import WhatsAppService

    service = WhatsAppService()
    return {"templates": service.list_content_templates()}


# ─── YAML Import / Export ────────────────────────────────────────────

class YamlExportRequest(BaseModel):
    workflow_id: str


@router.get("/{workflow_id}/export-yaml")
async def export_workflow_yaml(
    workflow_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Export a workflow definition as YAML."""
    import yaml

    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, organization_id=current_user.organization_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    definition = dict(wf.definition or {})
    definition["name"] = wf.name
    definition["description"] = wf.description or ""
    definition["category"] = wf.category or "custom"

    yaml_str = yaml.dump(definition, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return Response(
        content=yaml_str,
        media_type="text/yaml",
        headers={"Content-Disposition": f"attachment; filename={wf.name or 'workflow'}.yaml"},
    )


class YamlImportRequest(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    yaml_content: str


@router.post("/import-yaml")
async def import_workflow_yaml(
    body: YamlImportRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(database.get_db),
):
    """Import a workflow definition from YAML."""
    import yaml

    service = WorkflowService(db)
    try:
        definition = yaml.safe_load(body.yaml_content)
    except yaml.YAMLError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid YAML: {exc}")

    if not isinstance(definition, dict):
        raise HTTPException(status_code=422, detail="YAML must be a mapping")

    # Extract metadata from definition if not provided separately
    name = body.name or definition.pop("name", "Imported Workflow")
    description = body.description or definition.pop("description", None)
    category = body.category or definition.pop("category", "custom")

    try:
        wf = service.create_workflow(
            name=name,
            definition=definition,
            description=description,
            category=category,
            created_by=current_user.id,
            organization_id=current_user.organization_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _workflow_dict(wf)
