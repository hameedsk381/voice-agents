"""Phase 3 workflow automation tests."""
import pytest

from app.workflows.call_outcome import map_call_to_workflow_outcome, build_call_end_event


def test_map_success_outcome():
    assert map_call_to_workflow_outcome(analytics_outcome="SUCCESS") == "success"


def test_map_promise_from_summary():
    assert (
        map_call_to_workflow_outcome(
            analytics_outcome="SUCCESS",
            short_summary="Customer promised to pay next week",
        )
        == "promise_to_pay"
    )


def test_map_busy_end_reason():
    assert map_call_to_workflow_outcome(end_reason="line-busy") == "busy"


def test_build_call_end_event():
    event = build_call_end_event(
        analytics_outcome="FAILURE",
        end_reason="no-answer",
        session_id="sess-1",
    )
    assert event["last_call_outcome"] == "no_answer"
    assert event["last_session_id"] == "sess-1"


@pytest.mark.asyncio
async def test_advance_on_call_ended_no_contact(mock_db):
    from app.services.workflow_service import WorkflowService

    svc = WorkflowService(mock_db)
    result = await svc.advance_on_call_ended(contact_id=None)
    assert result["skipped"] is True
