"""A1 integration: SQLite repositories honour optimistic concurrency and leases."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from qa_contracts.errors import Conflict, NotFound
from qa_contracts.knowledge import (
    BlobRef,
    CreateKB,
    KnowledgeBase,
    Revision,
    Snapshot,
    Source,
    SourceManifest,
    UploadManifest,
    utc_now,
)
from qa_contracts.operations import Job, JobCommand, JobKind, JobState
from qa_infrastructure.repositories import SQLiteJobRepository, SQLiteKnowledgeRepository


async def test_store_requires_explicit_migration(tmp_path) -> None:
    from qa_infrastructure.sqlite import SQLiteStore

    store = SQLiteStore(tmp_path / "var" / "qa.sqlite3")
    with pytest.raises(FileNotFoundError):
        await store.open()
    assert not (tmp_path / "var").exists()
    result = await store.migrate("head")
    assert result.applied
    assert result.version >= 1
    await store.open()
    try:
        tables = {
            row["name"] for row in await store.fetchall(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        for table in ("kbs", "documents", "revisions", "snapshots", "jobs", "source_baselines"):
            assert table in tables
    finally:
        await store.close()


async def test_knowledge_repository_etag_conflict(
    knowledge: SQLiteKnowledgeRepository,
) -> None:
    kb = KnowledgeBase(
        kb_id="kb1", name="产品", description="", etag="v1", updated_at=utc_now()
    )
    await knowledge.put(kb, None)
    with pytest.raises(Conflict):
        await knowledge.put(kb, None)

    renamed = kb.model_copy(update={"name": "运维", "etag": "v2"})
    assert (await knowledge.put(renamed, "v1")).name == "运维"
    with pytest.raises(Conflict):
        await knowledge.put(renamed.model_copy(update={"etag": "v3"}), "v1")

    page = await knowledge.list()
    assert [item.kb_id for item in page.items] == ["kb1"]
    with pytest.raises(NotFound):
        await knowledge.get("missing")


async def test_source_revision_is_optimistic(sources) -> None:
    source = Source(
        source_id="src1", kb_id="kb1", kind="local_root", root_id="root1",
        display_name="docs", revision="r1",
    )
    await sources.put(source, None)
    with pytest.raises(Conflict):
        await sources.put(source.model_copy(update={"revision": "r2"}), "stale")
    await sources.put(source.model_copy(update={"revision": "r2"}), "r1")


async def test_content_revision_chain_and_conflict(content) -> None:
    from qa_contracts.knowledge import ContentKind

    first = Revision(
        revision_id="rev1", document_id="doc1", content_kind=ContentKind.DOCUMENT,
        normalized_text="第一版",
    )
    await content.append_revision("doc1", first, None, kb_id="kb1", title="文档一")
    detail = await content.get("doc1")
    assert detail.revision.normalized_text == "第一版"

    second = Revision(
        revision_id="rev2", document_id="doc1", parent_revision_id="rev1",
        content_kind=ContentKind.DOCUMENT, normalized_text="第二版",
    )
    with pytest.raises(Conflict):
        await content.append_revision("doc1", second, "rev-x", kb_id="kb1", title="文档一")
    await content.append_revision("doc1", second, "rev1", kb_id="kb1", title="文档一")
    detail = await content.get("doc1")
    assert detail.document.latest_revision_id == "rev2"
    older = await content.get("doc1", "rev1")
    assert older.revision.normalized_text == "第一版"


async def test_snapshot_compare_and_swap_active(snapshots) -> None:
    from qa_contracts.knowledge import SnapshotState

    await _kb(snapshots._store, "kb1")
    await snapshots.save(
        Snapshot(
            version_id="v1", kb_id="kb1", state=SnapshotState.READY,
            keyword_profile="zh", keyword_index_ref="ref", document_revisions={"doc": "rev"},
        )
    )
    assert await snapshots.compare_and_swap_active("kb1", None, "v1") is True
    assert await snapshots.compare_and_swap_active("kb1", None, "v1") is False
    assert await snapshots.compare_and_swap_active("kb1", "v1", "v2") is True
    assert len(await snapshots.list("kb1")) == 1


async def test_job_lease_recovery_and_idempotent_enqueue(jobs: SQLiteJobRepository) -> None:
    command = JobCommand(kind=JobKind.IMPORT, payload={"kb_id": "kb1"}, idempotency_key="key-1")
    first = await jobs.enqueue(command, "job1")
    replay = await jobs.enqueue(command, "job2")
    assert replay.job_id == first.job_id == "job1"
    assert first.state == JobState.QUEUED

    expired = datetime.now(UTC) - timedelta(seconds=1)
    claimed = await jobs.claim(JobKind.IMPORT.value, "worker-a", expired)
    assert claimed is not None and claimed.state == JobState.RUNNING
    assert await jobs.claim(JobKind.IMPORT.value, "worker-b", datetime.now(UTC)) is None

    recovered = await jobs.recover(datetime.now(UTC))
    assert [job.job_id for job in recovered] == ["job1"]
    assert recovered[0].state == JobState.QUEUED

    updated = await jobs.update(
        recovered[0].model_copy(update={"state": JobState.SUCCEEDED, "progress": 1.0}),
        recovered[0].revision,
    )
    assert updated.state == JobState.SUCCEEDED
    with pytest.raises(Conflict):
        await jobs.update(updated, recovered[0].revision)


async def test_job_events_are_sequenced_and_replayable(jobs) -> None:
    from qa_contracts.operations import JobEvent

    await jobs.enqueue(JobCommand(kind=JobKind.IMPORT), "job1")
    for _ in range(3):
        await jobs.append_event("job1", JobEvent(job_id="job1", seq=1, event="job.progress"))
    events = await jobs.read_events("job1", 0, 10)
    assert [event.seq for event in events] == [1, 2, 3]
    assert [event.seq for event in await jobs.read_events("job1", 2, 10)] == [3]


async def test_idempotency_repository_rejects_changed_request(idempotency) -> None:
    from qa_contracts.errors import Conflict as ErrorConflict

    assert await idempotency.claim("p1", "import", "k", "hash-a", "job1") is None
    assert await idempotency.claim("p1", "import", "k", "hash-a", "job2") == "job1"
    with pytest.raises(ErrorConflict):
        await idempotency.claim("p1", "import", "k", "hash-b", "job3")


async def test_blob_store_is_content_addressed(blobs) -> None:
    import hashlib

    first = await blobs.put_bytes(b"hello")
    second = await blobs.put_bytes(b"hello")
    assert first == second == hashlib.sha256(b"hello").hexdigest()
    assert await blobs.verify(first) is True
    assert (await blobs.read_bytes(first)) == b"hello"
    assert await blobs.verify("0" * 64) is False
    assert await blobs.verify("x") is False
    assert await blobs.delete_unreferenced([first]) == 1
    assert await blobs.verify(first) is False


async def _kb(store, kb_id: str) -> None:
    await SQLiteKnowledgeRepository(store).put(
        KnowledgeBase(kb_id=kb_id, name=kb_id, etag="e1", updated_at=utc_now()), None
    )


def test_manifest_and_blob_models_do_not_accept_escapes() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        UploadManifest.model_validate(
            {"source_id": "s", "files": [{"relative_path": "../x", "digest": "d", "size": 1}]}
        )
    with pytest.raises(ValidationError):
        SourceManifest(source_id="s", scan_scope="partial", scan_status="succeeded", complete=True)


def test_blob_ref_requires_digest() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BlobRef(digest="", size=0)
    assert Snapshot.model_fields["state"].default.value == "draft"


def test_create_kb_requires_name() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CreateKB(name="")


def test_job_model_rejects_bad_progress() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Job(job_id="j", kind=JobKind.IMPORT, revision=0, progress=2.0)
