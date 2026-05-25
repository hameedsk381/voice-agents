"""
Temporal workflow that periodically resumes in-app workflow instances past wait_until.
"""
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.orchestration.workflow_activities import process_due_workflow_instances_activity


@workflow.defn
class WorkflowDueSchedulerWorkflow:
    """Long-running scheduler; invoke once per environment (singleton workflow id)."""

    @workflow.run
    async def run(self, interval_seconds: int = 60, batch_limit: int = 100) -> None:
        while True:
            await workflow.execute_activity(
                process_due_workflow_instances_activity,
                batch_limit,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            await workflow.sleep(timedelta(seconds=max(interval_seconds, 15)))
