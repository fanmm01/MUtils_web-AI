"""Job cancellation semantics: never claim a stop the worker has not confirmed.

A queued job has written nothing, so it may become ``cancelled`` at once. A
running job only becomes ``cancel_requested``; the worker confirms at a safe
point and no snapshot is activated. These regressions cover both races.
"""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from kb_management.indexing import BuildOutcome, BuildRequest, IndexBuilder
from qa_contracts.knowledge import ChunkProfile, ManifestFile, SourceManifest
from qa_contracts.operations import JobCommand, JobKind, JobState
from qa_service.worker import _finish


def _prepare_running_job(client: TestClient) -> str:
    """Create a queued import job for cancellation tests."""
    kb = client.post("/v1/kbs", json={"name": "取消测试"}).json()
    client.post(
        f"/v1/kbs/{kb['kb_id']}/sources",
        json={
            "source_id": "src_cancel", "kb_id": kb["kb_id"], "kind": "upload",
            "display_name": "upload", "revision": "r1",
        },
    )
    # An empty but complete upload batch is a legitimate preview input; its
    # preview is empty, which is enough to exercise job state.
    batch = client.post(
        "/v1/uploads", json={"source_id": "src_cancel", "files": []}
    ).json()["batch_id"]
    client.post(f"/v1/uploads/{batch}/complete")
    preview = client.post(
        f"/v1/kbs/{kb['kb_id']}/imports/preview",
        json={"kb_id": kb["kb_id"], "source_id": "src_cancel"},
    ).json()
    applied = client.post(
        f"/v1/kbs/{kb['kb_id']}/imports",
        json={
            "kb_id": kb["kb_id"], "source_id": "src_cancel",
            "expected_preview_hash": preview["preview_hash"],
        },
    ).json()
    return applied["job_id"]


def test_queued_job_can_be_cancelled_immediately(api: TestClient) -> None:
    job_id = _prepare_running_job(api)
    response = api.post(f"/v1/jobs/{job_id}/cancel")
    assert response.status_code == 200, response.text
    assert response.json()["state"] == "cancelled"
    events = api.get(f"/v1/jobs/{job_id}/events").json()
    assert [event["event"] for event in events] == ["job.cancelled"]

    again = api.post(f"/v1/jobs/{job_id}/cancel")
    assert again.status_code == 409


def test_running_job_cancel_is_a_request_not_a_claim(api: TestClient) -> None:
    job_id = _prepare_running_job(api)
    jobs = api.app.state.container.jobs
    assert jobs is not None
    claimed = asyncio.run(
        jobs.claim(JobKind.IMPORT.value, "worker-a", _future())
    )
    assert claimed is not None and claimed.job_id == job_id
    assert claimed.state == JobState.RUNNING

    response = api.post(f"/v1/jobs/{job_id}/cancel")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["state"] == "cancel_requested"
    events = api.get(f"/v1/jobs/{job_id}/events").json()
    assert "job.cancelled" not in [event["event"] for event in events]
    assert events[-1]["data"]["phase"] == "cancel_requested"

    repeated = api.post(f"/v1/jobs/{job_id}/cancel")
    assert repeated.status_code == 200
    assert repeated.json()["state"] == "cancel_requested"


def test_worker_confirms_cancellation_and_does_not_activate_a_version(
    api: TestClient,
) -> None:
    job_id = _prepare_running_job(api)
    jobs = api.app.state.container.jobs
    assert jobs is not None
    claimed = asyncio.run(jobs.claim(JobKind.IMPORT.value, "worker-a", _future()))
    assert claimed is not None
    api.post(f"/v1/jobs/{job_id}/cancel")

    # A build that finishes after the cancel must not be reported as success.
    final = asyncio.run(
        _finish(jobs, claimed, JobState.SUCCEEDED, event="job.completed", progress=1.0)
    )
    assert final == job_id
    job = api.get(f"/v1/jobs/{job_id}").json()
    assert job["state"] == "cancelled"
    assert job["result_version_id"] is None
    events = api.get(f"/v1/jobs/{job_id}/events").json()
    assert events[-1]["event"] == "job.cancelled"
    assert "job.completed" not in [event["event"] for event in events]


def test_worker_reports_failure_after_cancel_as_cancelled(api: TestClient) -> None:
    job_id = _prepare_running_job(api)
    jobs = api.app.state.container.jobs
    assert jobs is not None
    claimed = asyncio.run(jobs.claim(JobKind.IMPORT.value, "worker-a", _future()))
    assert claimed is not None
    api.post(f"/v1/jobs/{job_id}/cancel")
    asyncio.run(
        _finish(
            jobs, claimed, JobState.FAILED, event="job.failed", error_code="IMPORT_FAILED"
        )
    )
    assert api.get(f"/v1/jobs/{job_id}").json()["state"] == "cancelled"


def _future():  # type: ignore[no-untyped-def]
    from datetime import UTC, datetime, timedelta

    return datetime.now(UTC) + timedelta(seconds=60)


class _Cancelling:
    def __init__(self, cancel_after: int) -> None:
        self.calls = 0
        self.cancel_after = cancel_after

    async def __call__(self) -> bool:
        self.calls += 1
        return self.calls > self.cancel_after


async def test_cancelled_build_discards_staging_and_commits_nothing(
    store, knowledge, sources, content, snapshots, snapshot_files, tmp_path: Path
) -> None:
    from kb_management.parsers import ParserRegistry
    from kb_management.service import KBService
    from qa_contracts.knowledge import CreateKB
    from qa_infrastructure.indexes import BM25Index

    kb = await KBService(knowledge=knowledge).create(CreateKB(name="取消"))
    from qa_contracts.knowledge import Source

    await sources.put(
        Source(
            source_id="src_c", kb_id=kb.kb_id, kind="local_root", root_id="root1",
            display_name="c", revision="r1",
        ),
        None,
    )
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "a.md").write_text("# 标题\n\n正文内容。\n", encoding="utf-8")
    payload = (corpus / "a.md").read_bytes()
    manifest = SourceManifest(
        source_id="src_c",
        files=[
            ManifestFile(
                relative_path="a.md",
                digest=hashlib.sha256(payload).hexdigest(),
                size=len(payload),
            )
        ],
        scan_scope="full",
        scan_status="succeeded",
        complete=True,
    )
    splitter = _Splitter()
    builder = IndexBuilder(
        knowledge=knowledge,
        sources=sources,
        content=content,
        snapshots=snapshots,
        files=snapshot_files,
        parser=ParserRegistry(),
        splitter=splitter,
        keyword_writer=BM25Index(tmp_path / "indexes"),
        chunk_profile=ChunkProfile(target_tokens=50, overlap_tokens=5),
        store=store,
    )
    outcome = await builder.build(
        BuildRequest(
            kb_id=kb.kb_id,
            source_id="src_c",
            manifest=manifest,
            files={"a.md": corpus / "a.md"},
            should_cancel=_Cancelling(cancel_after=0),
        )
    )
    assert isinstance(outcome, BuildOutcome)
    assert outcome.cancelled is True
    assert outcome.failed is False
    assert outcome.snapshot is None
    assert splitter.splits == 0, "no parsing/chunking may run after cancellation"
    assert await snapshots.list(kb.kb_id) == []
    assert await sources.has_baseline("src_c") is False
    assert not list((tmp_path / "var" / "snapshots" / "staging").glob("*"))


async def test_cancel_between_files_does_not_commit(
    store, knowledge, sources, content, snapshots, snapshot_files, tmp_path: Path
) -> None:
    from kb_management.parsers import ParserRegistry
    from kb_management.service import KBService
    from qa_contracts.knowledge import CreateKB, Source
    from qa_infrastructure.indexes import BM25Index

    kb = await KBService(knowledge=knowledge).create(CreateKB(name="取消二"))
    await sources.put(
        Source(
            source_id="src_d", kb_id=kb.kb_id, kind="local_root", root_id="root1",
            display_name="d", revision="r1",
        ),
        None,
    )
    corpus = tmp_path / "corpus2"
    corpus.mkdir()
    for name in ("a.md", "b.md"):
        (corpus / name).write_text(f"# {name}\n\n内容。\n", encoding="utf-8")
    manifest = SourceManifest(
        source_id="src_d",
        files=[
            ManifestFile(
                relative_path=name,
                digest=hashlib.sha256((corpus / name).read_bytes()).hexdigest(),
                size=(corpus / name).stat().st_size,
            )
            for name in ("a.md", "b.md")
        ],
        scan_scope="full",
        scan_status="succeeded",
        complete=True,
    )
    splitter = _Splitter()
    builder = IndexBuilder(
        knowledge=knowledge,
        sources=sources,
        content=content,
        snapshots=snapshots,
        files=snapshot_files,
        parser=ParserRegistry(),
        splitter=splitter,
        keyword_writer=BM25Index(tmp_path / "indexes"),
        chunk_profile=ChunkProfile(target_tokens=50, overlap_tokens=5),
        store=store,
    )
    outcome = await builder.build(
        BuildRequest(
            kb_id=kb.kb_id,
            source_id="src_d",
            manifest=manifest,
            files={name: corpus / name for name in ("a.md", "b.md")},
            should_cancel=_Cancelling(cancel_after=2),
        )
    )
    assert outcome.cancelled is True
    assert outcome.snapshot is None
    assert splitter.splits <= 1
    assert await snapshots.list(kb.kb_id) == []
    assert await sources.has_baseline("src_d") is False


class _Splitter:
    def __init__(self) -> None:
        self.splits = 0

    def split(self, document, *, kb_id, version_id, revision_id, profile):  # type: ignore[no-untyped-def]
        from qa_contracts.knowledge import Chunk, Locator

        self.splits += 1
        return [
            Chunk(
                chunk_id=f"{revision_id}-{index}",
                kb_id=kb_id,
                version_id=version_id,
                revision_id=revision_id,
                content_hash=hashlib.sha256(block.text.encode()).hexdigest(),
                text=block.text,
                locator=Locator(kind="text_lines", start_line=1, end_line=1),
                ordinal=index,
            )
            for index, block in enumerate(document.blocks)
        ]


def test_terminal_jobs_cannot_be_cancelled(api: TestClient) -> None:
    job_id = _prepare_running_job(api)
    assert api.post(f"/v1/jobs/{job_id}/cancel").json()["state"] == "cancelled"
    again = api.post(f"/v1/jobs/{job_id}/cancel")
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "CONFLICT"


async def test_expired_cancel_request_is_reconciled_to_cancelled(jobs) -> None:
    from datetime import UTC, datetime, timedelta

    await jobs.enqueue(
        JobCommand(kind=JobKind.IMPORT, payload={"kind": "import"}), "job-c"
    )
    claimed = await jobs.claim(
        JobKind.IMPORT.value, "worker-a", datetime.now(UTC) - timedelta(seconds=1)
    )
    assert claimed is not None and claimed.job_id == "job-c"
    await jobs.update(
        claimed.model_copy(update={"state": JobState.CANCEL_REQUESTED}), claimed.revision
    )
    recovered = await jobs.recover(datetime.now(UTC))
    assert [job.state for job in recovered] == [JobState.CANCELLED]
    events = await jobs.read_events("job-c", 0, 10)
    assert [event.event.value for event in events] == ["job.cancelled"]


async def test_expired_running_job_is_requeued(jobs) -> None:
    from datetime import UTC, datetime, timedelta

    await jobs.enqueue(
        JobCommand(kind=JobKind.IMPORT, payload={"kind": "import"}), "job-q"
    )
    claimed = await jobs.claim(
        JobKind.IMPORT.value, "worker-b", datetime.now(UTC) - timedelta(seconds=1)
    )
    assert claimed is not None
    recovered = await jobs.recover(datetime.now(UTC))
    assert [job.state for job in recovered] == [JobState.QUEUED]


class _CancelAfterKeywordBuild:
    """Simulates cancel_requested arriving while the keyword index is built."""

    def __init__(self) -> None:
        self.building = False
        self.built = False

    async def build(self, chunks, profile):  # type: ignore[no-untyped-def]
        self.building = True
        self.built = True
        return "index-ref"

    async def should_cancel(self) -> bool:
        return self.built


class _CancelAfterSeal:
    """Simulates cancel_requested arriving after files are sealed."""

    def __init__(self, inner) -> None:  # type: ignore[no-untyped-def]
        self._inner = inner
        self.sealed = False

    def __getattr__(self, name):  # type: ignore[no-untyped-def]
        return getattr(self._inner, name)

    async def seal(self, handle, *, kb_id, version_id):  # type: ignore[no-untyped-def]
        result = await self._inner.seal(handle, kb_id=kb_id, version_id=version_id)
        self.sealed = True
        return result

    async def should_cancel(self) -> bool:
        return self.sealed


async def _builder_for_cancel_race(
    store, knowledge, sources, content, snapshots, snapshot_files, tmp_path,
    keyword_writer, files_wrapper=None,
):  # type: ignore[no-untyped-def]
    import hashlib as _hashlib
    from pathlib import Path as _Path

    from kb_management.parsers import ParserRegistry
    from kb_management.service import KBService
    from qa_contracts.knowledge import CreateKB, ManifestFile, Source, SourceManifest

    kb = await KBService(knowledge=knowledge).create(CreateKB(name="竞态"))
    await sources.put(
        Source(
            source_id="src_race", kb_id=kb.kb_id, kind="local_root", root_id="root1",
            display_name="race", revision="r1",
        ),
        None,
    )
    corpus = _Path(tmp_path) / "race"
    corpus.mkdir()
    (corpus / "a.md").write_text("# 标题\n\n新内容。\n", encoding="utf-8")
    payload = (corpus / "a.md").read_bytes()
    manifest = SourceManifest(
        source_id="src_race",
        files=[
            ManifestFile(
                relative_path="a.md",
                digest=_hashlib.sha256(payload).hexdigest(),
                size=len(payload),
            )
        ],
        scan_scope="full",
        scan_status="succeeded",
        complete=True,
    )
    builder = IndexBuilder(
        knowledge=knowledge,
        sources=sources,
        content=content,
        snapshots=snapshots,
        files=files_wrapper or snapshot_files,
        parser=ParserRegistry(),
        splitter=_Splitter(),
        keyword_writer=keyword_writer,
        chunk_profile=ChunkProfile(target_tokens=50, overlap_tokens=5),
        store=store,
    )
    return kb, builder, corpus, manifest


async def test_cancel_during_keyword_build_commits_nothing(
    store, knowledge, sources, content, snapshots, snapshot_files, tmp_path
) -> None:
    gate = _CancelAfterKeywordBuild()
    kb, builder, corpus, manifest = await _builder_for_cancel_race(
        store, knowledge, sources, content, snapshots, snapshot_files, tmp_path, gate
    )
    outcome = await builder.build(
        BuildRequest(
            kb_id=kb.kb_id,
            source_id="src_race",
            manifest=manifest,
            files={"a.md": corpus / "a.md"},
            should_cancel=gate.should_cancel,
        )
    )
    assert gate.building and gate.built
    assert outcome.cancelled is True
    assert outcome.snapshot is None
    assert await snapshots.list(kb.kb_id) == []
    assert await sources.has_baseline("src_race") is False
    assert not list((tmp_path / "var" / "snapshots" / "staging").glob("*"))


async def test_cancel_after_seal_does_not_commit_snapshot_or_baseline(
    store, knowledge, sources, content, snapshots, snapshot_files, tmp_path
) -> None:
    from qa_infrastructure.indexes import BM25Index

    gate = _CancelAfterSeal(snapshot_files)
    kb, builder, corpus, manifest = await _builder_for_cancel_race(
        store, knowledge, sources, content, snapshots, snapshot_files, tmp_path,
        BM25Index(tmp_path / "indexes"), files_wrapper=gate,
    )
    outcome = await builder.build(
        BuildRequest(
            kb_id=kb.kb_id,
            source_id="src_race",
            manifest=manifest,
            files={"a.md": corpus / "a.md"},
            should_cancel=gate.should_cancel,
        )
    )
    assert gate.sealed is True
    assert outcome.cancelled is True
    assert outcome.snapshot is None
    assert await snapshots.list(kb.kb_id) == []
    assert await sources.has_baseline("src_race") is False
