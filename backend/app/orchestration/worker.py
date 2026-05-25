"""
Temporal worker that executes workflow activities.
"""
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from loguru import logger

from app.orchestration.workflows import (
    CallWorkflow,
    initialize_session,
    process_user_input,
    generate_response,
    synthesize_audio,
    execute_tool_activity,
    transfer_to_human,
    end_session_activity,
)
from app.orchestration.workflow_scheduler import WorkflowDueSchedulerWorkflow
from app.orchestration.workflow_activities import process_due_workflow_instances_activity
from app.core.config import settings


async def create_temporal_client() -> Client:
    """Create a Temporal client connection."""
    return await Client.connect(settings.TEMPORAL_HOST)


async def start_worker():
    """Start the Temporal worker."""
    client = await create_temporal_client()
    
    worker = Worker(
        client,
        task_queue="voice-agent-queue",
        workflows=[CallWorkflow, WorkflowDueSchedulerWorkflow],
        activities=[
            initialize_session,
            process_user_input,
            generate_response,
            synthesize_audio,
            execute_tool_activity,
            transfer_to_human,
            end_session_activity,
            process_due_workflow_instances_activity,
        ],
    )
    
    logger.info("Starting Temporal worker on queue: voice-agent-queue")
    await worker.run()


async def start_workflow(session_id: str, agent_id: str, caller_id: str = None):
    """Start a new call workflow."""
    from app.orchestration.workflows import CallInput
    
    client = await create_temporal_client()
    
    input_data = CallInput(
        session_id=session_id,
        agent_id=agent_id,
        caller_id=caller_id,
        call_type="inbound"
    )
    
    handle = await client.start_workflow(
        CallWorkflow.run,
        input_data,
        id=f"call-{session_id}",
        task_queue="voice-agent-queue"
    )
    
    logger.info(f"Started workflow for session {session_id}")
    return handle


async def signal_user_input(session_id: str, text: str):
    """Send user input to a running workflow."""
    client = await create_temporal_client()
    
    handle = client.get_workflow_handle(f"call-{session_id}")
    await handle.signal(CallWorkflow.receive_user_input, text)


async def end_workflow(session_id: str):
    """Signal a workflow to end."""
    client = await create_temporal_client()
    
    handle = client.get_workflow_handle(f"call-{session_id}")
    await handle.signal(CallWorkflow.end_call)


async def get_workflow_status(session_id: str) -> dict:
    """Query workflow status."""
    client = await create_temporal_client()
    
    handle = client.get_workflow_handle(f"call-{session_id}")
    return await handle.query(CallWorkflow.get_status)


async def ensure_workflow_scheduler(interval_seconds: int = 60) -> None:
    """Start the due-instance scheduler workflow if not already running."""
    client = await create_temporal_client()
    workflow_id = "voise-workflow-due-scheduler"
    try:
        handle = client.get_workflow_handle(workflow_id)
        await handle.describe()
        logger.info(f"Workflow scheduler already running: {workflow_id}")
    except Exception:
        await client.start_workflow(
            WorkflowDueSchedulerWorkflow.run,
            interval_seconds,
            id=workflow_id,
            task_queue="voice-agent-queue",
        )
        logger.info(f"Started workflow scheduler: {workflow_id}")


if __name__ == "__main__":
    async def _main():
        await ensure_workflow_scheduler()
        await start_worker()

    asyncio.run(_main())
