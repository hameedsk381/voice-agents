"""Workflow definition and engine tests."""
import pytest

from app.workflows.engine import WorkflowEngine
from app.workflows.schema import WorkflowDefinitionV1
from app.workflows.templates import COLLECTIONS_PAYMENT_REMINDER


def test_collections_template_validates():
    defn = WorkflowDefinitionV1.model_validate(COLLECTIONS_PAYMENT_REMINDER)
    defn.validate_graph()
    assert defn.entry == "check_vip"
    assert len(defn.nodes) >= 10


def test_condition_eval():
    from app.workflows.engine import _eval_condition
    from app.workflows.schema import WorkflowNode, NodeType

    node = WorkflowNode(
        id="c1",
        type=NodeType.CONDITION,
        config={"rules": [{"field": "aging_days", "op": "gte", "value": 120}]},
        on_true="yes",
        on_false="no",
    )
    assert _eval_condition(node, {"aging_days": 150}) is True
    assert _eval_condition(node, {"aging_days": 30}) is False


@pytest.mark.asyncio
async def test_engine_end_node(mock_db):
    engine = WorkflowEngine(mock_db)
    defn = WorkflowDefinitionV1.model_validate(
        {
            "version": "1",
            "entry": "end1",
            "nodes": [
                {"id": "end1", "type": "end", "config": {"outcome": "done"}},
            ],
        }
    )
    result = await engine.run_until_wait_or_done(
        defn,
        current_node_id="end1",
        context={},
        instance_meta={},
    )
    assert result["status"] == "completed"
    assert result["context"]["workflow_outcome"] == "done"
