"""Job and widget-ticket routes (A1 owner).

Job state is durable (SQLite); events are persisted before they are streamed, so
a reconnect with ``Last-Event-ID`` replays without re-running the job.
"""

from __future__ import annotations

from fastapi import APIRouter, Header

from qa_contracts.base import ContractModel
from qa_contracts.errors import (
    Conflict,
    ErrorDetail,
    FeatureNotImplemented,
    ValidationFailed,
)
from qa_contracts.operations import Job, JobEvent, JobState

from ..deps import ContainerDep, services_for

router = APIRouter(tags=["operations"])


class JobEventEnvelope(ContractModel):
    """P2 JSON replay; distinct from the future SSE representation."""

    id: int
    event: str
    data: JobEvent


@router.get("/v1/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str, container: ContainerDep) -> Job:
    services = await services_for(container)
    return await services.container.jobs.get(job_id)  # type: ignore[union-attr]


@router.get(
    "/v1/jobs/{job_id}/events",
    response_model=list[JobEventEnvelope],
    responses={
        200: {
            "description": "Persisted JSON replay; SSE is not yet implemented",
            "content": {
                "application/json": {"schema": {
                    "type": "array", "items": {"$ref": "#/components/schemas/JobEventEnvelope"}
                }},
                "text/event-stream": {
                    "schema": {"type": "string"},
                    "description": "Reserved for negotiated P3 SSE; currently returns 501",
                },
            },
        }
    },
)
async def job_events(
    job_id: str,
    container: ContainerDep,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    accept: str | None = Header(default=None, alias="Accept"),
) -> list[JobEventEnvelope]:
    """Persisted event replay as JSON.

    The streaming form is P3; until then a client can poll this endpoint and get
    the same persisted events with stable sequence numbers.
    """
    if accept and "text/event-stream" in accept.lower():
        raise FeatureNotImplemented("job SSE")
    services = await services_for(container)
    jobs = services.container.jobs
    assert jobs is not None
    await jobs.get(job_id)
    after = _cursor(last_event_id)
    events = await jobs.read_events(job_id, after, 200)
    return [JobEventEnvelope(id=event.seq, event=event.event.value, data=event) for event in events]


@router.post("/v1/jobs/{job_id}/cancel", response_model=Job)
async def cancel_job(job_id: str, container: ContainerDep) -> Job:
    """Request cancellation without lying about work that is still running.

    A queued job has not written anything, so it becomes ``cancelled`` at once.
    A running job only enters ``cancel_requested``; the worker confirms the
    terminal state at its next safe point, because it may hold a transaction
    mid-write. Claiming ``cancelled`` here could hide a snapshot that later
    becomes active.
    """
    services = await services_for(container)
    jobs = services.container.jobs
    assert jobs is not None
    job = await jobs.get(job_id)
    if job.state == JobState.CANCEL_REQUESTED:
        return job
    if job.state == JobState.QUEUED:
        cancelled = await jobs.update(
            job.model_copy(update={"state": JobState.CANCELLED}), job.revision
        )
        await jobs.append_event(
            job_id, JobEvent(job_id=job_id, seq=1, event="job.cancelled")
        )
        return cancelled
    if job.state != JobState.RUNNING:
        raise Conflict("a queued or running job", f"state {job.state.value}")
    requested = await jobs.update(
        job.model_copy(update={"state": JobState.CANCEL_REQUESTED}), job.revision
    )
    await jobs.append_event(
        job_id,
        JobEvent(
            job_id=job_id, seq=1, event="job.progress", phase="cancel_requested",
            progress=job.progress,
            diagnostic="cancellation requested; waiting for the worker to stop",
        ),
    )
    return requested


@router.post("/v1/widget/tickets", status_code=201)
async def issue_ticket(container: ContainerDep) -> None:
    await services_for(container)
    raise FeatureNotImplemented("widget")


def _cursor(value: str | None) -> int:
    if value is None:
        return 0
    try:
        cursor = int(value)
    except ValueError as exc:
        raise ValidationFailed(
            [ErrorDetail(field="Last-Event-ID", reason="must be an integer sequence")]
        ) from exc
    if cursor < 0:
        raise ValidationFailed(
            [ErrorDetail(field="Last-Event-ID", reason="must not be negative")]
        )
    return cursor


__all__ = ["router"]
