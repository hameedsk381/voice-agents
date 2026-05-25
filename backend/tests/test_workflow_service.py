"""
Tests for WorkflowService — CRUD, instance lifecycle, advance_instance, process_due.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Any, Dict

from app.services.workflow_service import WorkflowService
from app.models.workflow import Workflow, WorkflowInstance, WorkflowStatus, WorkflowInstanceStatus


SAMPLE_DEFINITION: Dict[str, Any] = {
    "version": "1",
    "entry": "start1",
    "nodes": [
        {"id": "start1", "type": "start", "next": "end1"},
        {"id": "end1", "type": "end", "config": {"outcome": "done"}},
    ],
}


def _fake_workflow(**kwargs) -> Workflow:
    defaults = dict(
        id="wf-1", name="Test WF", definition=SAMPLE_DEFINITION,
        version="1", status=WorkflowStatus.DRAFT.value,
        is_template=False, organization_id="default",
    )
    defaults.update(kwargs)
    wf = Workflow(**defaults)
    return wf


def _fake_instance(**kwargs) -> WorkflowInstance:
    defaults = dict(
        id="inst-1", workflow_id="wf-1",
        status=WorkflowInstanceStatus.RUNNING.value,
        current_node_id="start1", context={},
        organization_id="default",
    )
    defaults.update(kwargs)
    return WorkflowInstance(**defaults)


# ─── Templates ───────────────────────────────────────────────────────

class TestTemplates:
    def test_list_templates(self, mock_db):
        svc = WorkflowService(mock_db)
        tpls = svc.list_templates()
        assert isinstance(tpls, list)
        assert len(tpls) > 0
        slugs = [t["slug"] for t in tpls]
        assert "collections-payment-reminder" in slugs

    def test_get_template_definition(self, mock_db):
        svc = WorkflowService(mock_db)
        tpl = svc.get_template_definition("collections-payment-reminder")
        assert tpl is not None
        assert tpl["name"] == "Collections — Payment Reminder"

    def test_get_template_definition_unknown(self, mock_db):
        svc = WorkflowService(mock_db)
        assert svc.get_template_definition("nonexistent") is None


# ─── Workflow CRUD ───────────────────────────────────────────────────

class TestWorkflowCRUD:
    def test_create_workflow(self, mock_db):
        svc = WorkflowService(mock_db)

        # Mock the DB add/commit/refresh
        def _refresh(wf):
            wf.id = "new-wf-id"
        mock_db.refresh.side_effect = _refresh

        wf = svc.create_workflow(
            name="My Workflow",
            definition=SAMPLE_DEFINITION,
            description="A test",
            category="custom",
            organization_id="default",
            created_by="user-1",
        )
        assert wf.name == "My Workflow"
        assert wf.organization_id == "default"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_workflow_from_template(self, mock_db):
        svc = WorkflowService(mock_db)

        def _refresh(wf):
            wf.id = "wf-from-tpl"
        mock_db.refresh.side_effect = _refresh

        wf = svc.create_workflow(
            name="From Template",
            definition={},
            from_template_slug="collections-payment-reminder",
            organization_id="default",
        )
        assert wf.name == "From Template"
        assert "nodes" in (wf.definition or {})

    def test_create_workflow_unknown_template_raises(self, mock_db):
        svc = WorkflowService(mock_db)
        with pytest.raises(ValueError, match="Unknown template"):
            svc.create_workflow(name="X", definition={}, from_template_slug="bogus")

    def test_list_workflows(self, mock_db):
        wf1 = _fake_workflow(id="wf-1")
        wf2 = _fake_workflow(id="wf-2")
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [wf1, wf2]

        svc = WorkflowService(mock_db)
        result = svc.list_workflows(organization_id="default")
        assert len(result) == 2

    def test_list_workflows_no_org(self, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        svc = WorkflowService(mock_db)
        result = svc.list_workflows()
        assert result == []

    def test_get_workflow(self, mock_db):
        wf = _fake_workflow()
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = wf

        svc = WorkflowService(mock_db)
        result = svc.get_workflow("wf-1", organization_id="default")
        assert result is not None
        assert result.id == "wf-1"

    def test_get_workflow_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        svc = WorkflowService(mock_db)
        assert svc.get_workflow("nonexistent") is None

    def test_update_workflow(self, mock_db):
        wf = _fake_workflow()
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = wf

        svc = WorkflowService(mock_db)
        result = svc.update_workflow("wf-1", name="Updated", organization_id="default")
        assert result is not None
        assert result.name == "Updated"

    def test_update_workflow_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        svc = WorkflowService(mock_db)
        assert svc.update_workflow("nonexistent", name="X") is None

    def test_delete_workflow(self, mock_db):
        wf = _fake_workflow()
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = wf

        svc = WorkflowService(mock_db)
        assert svc.delete_workflow("wf-1", organization_id="default") is True
        mock_db.delete.assert_called_once_with(wf)

    def test_delete_workflow_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        svc = WorkflowService(mock_db)
        assert svc.delete_workflow("nonexistent") is False

    def test_publish_workflow(self, mock_db):
        wf = _fake_workflow()
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = wf

        svc = WorkflowService(mock_db)
        result = svc.publish_workflow("wf-1", organization_id="default")
        assert result is not None
        assert result.status == WorkflowStatus.ACTIVE.value


# ─── Instance Lifecycle ──────────────────────────────────────────────

class TestInstanceLifecycle:
    @pytest.mark.asyncio
    async def test_create_instance(self, mock_db):
        wf = _fake_workflow()
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = wf

        def _refresh(inst):
            inst.id = "new-inst-id"
        mock_db.refresh.side_effect = _refresh

        svc = WorkflowService(mock_db)
        # Don't auto_start (avoids calling advance_instance)
        inst = await svc.create_instance(
            "wf-1",
            context={"customer": "Raj"},
            campaign_id="camp-1",
            organization_id="default",
            auto_start=False,
        )
        assert inst.status == WorkflowInstanceStatus.RUNNING.value
        assert inst.current_node_id == "start1"
        assert inst.context.get("customer") == "Raj"

    @pytest.mark.asyncio
    async def test_create_instance_with_auto_start(self, mock_db):
        wf = _fake_workflow()
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = wf

        def _refresh(inst):
            inst.id = "inst-auto"
        mock_db.refresh.side_effect = _refresh

        svc = WorkflowService(mock_db)

        # Simulate advance_instance returning the updated instance
        advanced_inst = _fake_instance(id="inst-auto", status=WorkflowInstanceStatus.COMPLETED.value, outcome="done")
        svc.advance_instance = AsyncMock(return_value=advanced_inst)

        inst = await svc.create_instance(
            "wf-1", context={}, organization_id="default", auto_start=True,
        )
        assert inst.status == WorkflowInstanceStatus.COMPLETED.value
        svc.advance_instance.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_instance_workflow_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        svc = WorkflowService(mock_db)
        with pytest.raises(ValueError, match="Workflow not found"):
            await svc.create_instance("nonexistent", context={})

    def test_get_instance(self, mock_db):
        inst = _fake_instance()
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = inst

        svc = WorkflowService(mock_db)
        result = svc.get_instance("inst-1", organization_id="default")
        assert result is not None
        assert result.id == "inst-1"

    def test_get_instance_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        svc = WorkflowService(mock_db)
        assert svc.get_instance("nonexistent") is None

    def test_list_instances(self, mock_db):
        inst1 = _fake_instance(id="inst-1")
        inst2 = _fake_instance(id="inst-2")
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [inst1, inst2]

        svc = WorkflowService(mock_db)
        result = svc.list_instances(workflow_id="wf-1", organization_id="default")
        assert len(result) == 2

    def test_list_instances_for_contact(self, mock_db):
        inst = _fake_instance()
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [inst]
        svc = WorkflowService(mock_db)
        result = svc.list_instances_for_contact("contact-1", organization_id="default")
        assert len(result) == 1

    def test_list_instances_for_campaign(self, mock_db):
        inst = _fake_instance()
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [inst]
        svc = WorkflowService(mock_db)
        result = svc.list_instances_for_campaign("camp-1", organization_id="default")
        assert len(result) == 1


# ─── advance_instance ────────────────────────────────────────────────

class TestAdvanceInstance:
    @staticmethod
    def _make_query_side_effect(wf, inst):
        def q_side(model):
            if model == Workflow:
                m = MagicMock()
                m.filter.return_value.first.return_value = wf
                m.filter.return_value.filter.return_value = m.filter.return_value
                return m
            if model == WorkflowInstance:
                m = MagicMock()
                m.filter.return_value.first.return_value = inst
                m.filter.return_value.filter.return_value = m.filter.return_value
                return m
            return MagicMock()
        return q_side

    @pytest.mark.asyncio
    async def test_advance_completes_workflow(self, mock_db):
        wf = _fake_workflow()
        inst = _fake_instance(current_node_id="start1")
        mock_db.query.side_effect = self._make_query_side_effect(wf, inst)

        svc = WorkflowService(mock_db)
        result = await svc.advance_instance("inst-1")

        assert result.status == WorkflowInstanceStatus.COMPLETED.value
        assert result.outcome == "done"

    @pytest.mark.asyncio
    async def test_advance_instance_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        svc = WorkflowService(mock_db)
        with pytest.raises(ValueError, match="Instance not found"):
            await svc.advance_instance("nonexistent")

    @pytest.mark.asyncio
    async def test_advance_with_event_merges(self, mock_db):
        wf = _fake_workflow()
        inst = _fake_instance(current_node_id="start1", context={"existing": "val"})
        mock_db.query.side_effect = self._make_query_side_effect(wf, inst)

        svc = WorkflowService(mock_db)
        result = await svc.advance_instance("inst-1", event={"last_call_outcome": "success"})

        ctx = result.context or {}
        assert ctx.get("existing") == "val"
        assert ctx.get("last_call_outcome") == "success"

    @pytest.mark.asyncio
    async def test_advance_skips_future_wait_until(self, mock_db):
        wf = _fake_workflow()
        future = datetime.utcnow() + timedelta(hours=1)
        inst = _fake_instance(
            status=WorkflowInstanceStatus.WAITING.value,
            wait_until=future,
        )
        mock_db.query.side_effect = self._make_query_side_effect(wf, inst)

        svc = WorkflowService(mock_db)
        result = await svc.advance_instance("inst-1", event={})
        assert result.status == WorkflowInstanceStatus.WAITING.value


# ─── process_due_instances ───────────────────────────────────────────

class TestProcessDue:
    @pytest.mark.asyncio
    async def test_process_due(self, mock_db):
        past = datetime.utcnow() - timedelta(minutes=10)
        inst1 = _fake_instance(id="due-1", status=WorkflowInstanceStatus.WAITING.value, wait_until=past)
        inst2 = _fake_instance(id="due-2", status=WorkflowInstanceStatus.WAITING.value, wait_until=past)
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = [inst1, inst2]

        svc = WorkflowService(mock_db)
        svc.advance_instance = AsyncMock()
        svc.advance_instance.return_value = _fake_instance(id="due-1")

        result = await svc.process_due_instances(limit=10, organization_id="default")
        assert result["processed"] == 2
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_process_due_empty(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = []
        svc = WorkflowService(mock_db)
        result = await svc.process_due_instances()
        assert result["processed"] == 0
        assert result["checked"] == 0


# ─── advance_on_call_ended ───────────────────────────────────────────

class TestAdvanceOnCallEnded:
    @pytest.mark.asyncio
    async def test_advance_on_call_ended(self, mock_db):
        inst = _fake_instance(contact_id="contact-1")

        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [inst]
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = inst

        svc = WorkflowService(mock_db)
        with patch.object(svc, 'advance_instance', new=AsyncMock()) as mock_advance:
            mock_advance.return_value = inst
            result = await svc.advance_on_call_ended(
                contact_id="contact-1",
                analytics_outcome="SUCCESS",
                end_reason="completed",
                short_summary="Good call",
                session_id="sess-1",
                call_id="call-1",
            )
        assert result["advanced"] == 1
