"""
Temporal activities for Voise workflow automation (Phase 2).
Wire these in workflow_activities when running the Temporal worker.
"""
from typing import Optional
from temporalio import activity

from app.core import database
from app.services.workflow_service import WorkflowService


@activity.defn
async def process_due_workflow_instances_activity(limit: int = 100, organization_id: Optional[str] = None) -> dict:
    db = database.SessionLocal()
    try:
        service = WorkflowService(db)
        return await service.process_due_instances(limit=limit, organization_id=organization_id)
    finally:
        db.close()
