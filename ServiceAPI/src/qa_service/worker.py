"""Background worker entry point (A1 owner).

The worker consumes persisted import jobs: claim → execute → persist events and
the resulting snapshot. It refuses to start when no migrated database exists
rather than pretending to consume a queue.
"""

from __future__ import annotations

import argparse
import asyncio
import signal
import threading
import uuid

from qa_contracts.errors import APIError, Conflict
from qa_contracts.operations import JobKind, JobState

from .container import Container, build_container, close_container
from .settings import load_settings

SUPPORTED_KINDS: tuple[JobKind, ...] = (
    JobKind.IMPORT,
    JobKind.MODEL_INSTALL,
    JobKind.MODEL_VERIFY,
)

LEASE_SECONDS = 120


def dispatch(job_kind: JobKind) -> None:
    """Model job kinds belong to P3; refuse them explicitly."""
    if job_kind in {JobKind.MODEL_INSTALL, JobKind.MODEL_VERIFY}:
        raise NotImplementedError(f"job kind {job_kind.value} is implemented in P3")
    raise NotImplementedError(f"job kind {job_kind.value} has no dispatcher")


async def run_once(container: Container, *, worker_id: str | None = None) -> str | None:
    """Claim and execute at most one import job. Returns the job id, if any."""
    from datetime import UTC, datetime, timedelta

    from qa_contracts.operations import JobEvent

    from .business import services

    if not container.opened:
        if container.store is None or not container.store.database_path.exists():
            raise SystemExit(
                "qa-worker: database is not initialized; run 'qa-migrate' first"
            )
        from .container import open_container

        await open_container(container)
    bundle = await services(container)
    jobs = container.jobs
    assert jobs is not None
    await jobs.recover(datetime.now(UTC))
    lease_until = datetime.now(UTC) + timedelta(seconds=LEASE_SECONDS)
    assigned_worker = worker_id or uuid.uuid4().hex
    job = await jobs.claim(JobKind.IMPORT.value, assigned_worker, lease_until)
    if job is None:
        return None
    await jobs.append_event(
        job.job_id, JobEvent(job_id=job.job_id, seq=1, event="job.progress", progress=0.0)
    )

    async def heartbeat() -> None:
        while True:
            await asyncio.sleep(LEASE_SECONDS / 3)
            renewed = await jobs.renew_lease(
                job.job_id,
                assigned_worker,
                datetime.now(UTC) + timedelta(seconds=LEASE_SECONDS),
            )
            if not renewed:
                return

    heartbeat_task = asyncio.create_task(heartbeat())

    async def cancelled() -> bool:
        current = await jobs.get(job.job_id)
        return current.state != JobState.RUNNING

    try:
        return await _execute_claimed_job(bundle, jobs, job, cancelled)
    finally:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass


async def _execute_claimed_job(bundle, jobs, job, cancelled) -> str:
    payload = await jobs.payload(job.job_id)
    files: dict[str, object] = {}
    source_id = str(payload.get("source_id", ""))
    try:
        source = await bundle.sources.get(source_id)
        files = bundle.imports.file_paths(source, _manifest(payload))
    except APIError:
        files = {}
    try:
        outcome = await bundle.imports.execute(  # type: ignore[arg-type]
            job, files=files, should_cancel=cancelled
        )
    except Conflict:
        # The cancel API changed the row while this build ran; read the truth.
        current = await jobs.get(job.job_id)
        if current.state == JobState.CANCEL_REQUESTED:
            await _confirm_cancel(jobs, current)
            return current.job_id
        raise
    except APIError as error:
        return await _finish(
            jobs, job, JobState.FAILED,
            error_code=error.code.value,
            event="job.failed",
            diagnostic=error.message,
        )
    if outcome.cancelled:
        return await _confirm_cancel(jobs, await jobs.get(job.job_id))
    if outcome.failed:
        return await _finish(
            jobs, job, JobState.FAILED,
            error_code="IMPORT_FAILED",
            diagnostics=outcome.diagnostics,
            event="job.failed",
            diagnostic=outcome.reason or "import produced no content",
        )
    snapshot = outcome.snapshot
    assert snapshot is not None
    # The snapshot is READY but not active: publishing is an explicit action, so
    # a cancel that raced this build still leaves the active version untouched.
    return await _finish(
        jobs, job, JobState.SUCCEEDED,
        progress=1.0,
        result_version_id=snapshot.version_id,
        diagnostics=outcome.diagnostics,
        event="job.completed",
    )


async def _finish(
    jobs: object,
    job: object,
    state: JobState,
    *,
    event: str,
    diagnostic: str | None = None,
    **fields: object,
) -> str:
    """Persist a terminal state unless a concurrent cancel got there first."""
    from qa_contracts.errors import Conflict as StateConflict
    from qa_contracts.operations import JobEvent

    updated = job.model_copy(
        update={"state": state, "worker_id": None, "lease_until": None, **fields}
    )
    try:
        result = await jobs.update_with_event(
            updated,
            job.revision,
            JobEvent(
                job_id=job.job_id,
                seq=1,
                event=event,  # type: ignore[arg-type]
                progress=fields.get("progress"),  # type: ignore[arg-type]
                diagnostic=diagnostic,
            ),
        )
    except StateConflict:
        current = await jobs.get(job.job_id)
        if current.state == JobState.CANCEL_REQUESTED:
            return await _confirm_cancel(jobs, current)
        raise
    return result.job_id


async def _confirm_cancel(jobs: object, job: object) -> str:
    from qa_contracts.operations import JobEvent

    confirmed = await jobs.update_with_event(
        job.model_copy(
            update={"state": JobState.CANCELLED, "worker_id": None, "lease_until": None}
        ),
        job.revision,
        JobEvent(
            job_id=job.job_id,
            seq=1,
            event="job.cancelled",
            diagnostic="worker stopped at a safe point; no snapshot was activated",
        ),
    )
    return confirmed.job_id


def _manifest(payload: dict[str, object]):  # type: ignore[no-untyped-def]
    from qa_contracts.knowledge import SourceManifest

    return SourceManifest.model_validate(payload["manifest"])


def run_worker(container: Container, stop_signal: threading.Event) -> None:
    async def loop() -> None:
        while not stop_signal.is_set():
            worked = await run_once(container)
            if worked is None:
                await asyncio.sleep(1.0)

    asyncio.run(loop())


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="qa-worker", description="Q&A assistant worker")
    parser.add_argument("--once", action="store_true", help="run a single poll cycle")
    args = parser.parse_args(argv)
    settings = load_settings()
    container = build_container(settings)
    stop = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())

    if args.once:
        async def single() -> str | None:
            try:
                return await run_once(container)
            finally:
                if container.store is not None:
                    await container.store.close()

        try:
            job_id = asyncio.run(single())
        except SystemExit as exc:
            raise SystemExit(str(exc)) from exc
        print("qa-worker: no queued import job" if job_id is None else f"qa-worker: {job_id}")
        return
    try:
        run_worker(container, stop)
    except SystemExit as exc:
        raise SystemExit(str(exc)) from exc
    finally:
        close_container(container)


if __name__ == "__main__":
    main()
