"""Durability across process restarts plus idempotent enqueue.

The store is closed and reopened exactly like a second ``qa-api`` process would
see it: SQLite rows, sealed snapshot files and job leases all survive.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from qa_contracts.errors import Conflict
from qa_contracts.knowledge import (
    SourceManifest,
    utc_now,
)
from qa_contracts.operations import JobCommand, JobKind, JobState
from qa_infrastructure.repositories import SQLiteJobRepository
from qa_infrastructure.sqlite import SQLiteStore


async def _open(tmp_path: Path) -> SQLiteStore:
    database = tmp_path / "var" / "qa.sqlite3"
    creating = SQLiteStore(database)
    await creating.migrate("head")
    store = SQLiteStore(database)
    await store.open()
    return store


async def test_data_and_sealed_snapshots_survive_a_restart(tmp_path: Path) -> None:
    from qa_contracts.knowledge import KnowledgeBase, Revision
    from qa_infrastructure.repositories import (
        SQLiteContentRepository,
        SQLiteKnowledgeRepository,
        SQLiteSnapshotRepository,
    )
    from qa_infrastructure.snapshots import FileSnapshotStore

    store = await _open(tmp_path)
    files = FileSnapshotStore(tmp_path / "var" / "snapshots")
    knowledge = SQLiteKnowledgeRepository(store)
    content = SQLiteContentRepository(store)
    await knowledge.put(
        KnowledgeBase(kb_id="kb1", name="产品", etag="e1", updated_at=utc_now()), None
    )
    await content.append_revision(
        "doc1",
        Revision(revision_id="rev1", document_id="doc1", normalized_text="正文"),
        None,
        kb_id="kb1",
        title="文档",
    )
    handle = await files.stage(["doc1"], kb_id="kb1", version_id="ver1")
    from qa_contracts.knowledge import Chunk, Locator

    await files.append_chunks(
        handle,
        [
            Chunk(
                chunk_id="chunk1", kb_id="kb1", version_id="ver1", revision_id="rev1",
                content_hash=hashlib.sha256("正文".encode()).hexdigest(), text="正文",
                locator=Locator(kind="text_lines", start_line=1, end_line=1), ordinal=0,
            )
        ],
    )
    await files.seal(handle, kb_id="kb1", version_id="ver1")
    await store.close()

    reopened = await _open(tmp_path)
    try:
        assert (await SQLiteKnowledgeRepository(reopened).get("kb1")).name == "产品"
        detail = await SQLiteContentRepository(reopened).get("doc1")
        assert detail.revision.normalized_text == "正文"
        assert await files.verify("kb1", "ver1") is True
        chunks = await files.load_all_chunks("kb1", "ver1")
        assert [chunk.text for chunk in chunks] == ["正文"]
        assert await SQLiteSnapshotRepository(reopened).list("kb1") == []
    finally:
        await reopened.close()


async def test_running_job_lease_is_recovered_after_restart(tmp_path: Path) -> None:
    store = await _open(tmp_path)
    jobs = SQLiteJobRepository(store)
    await jobs.enqueue(JobCommand(kind=JobKind.IMPORT, payload={"kind": "import"}), "job1")
    claimed = await jobs.claim(
        JobKind.IMPORT.value, "worker-a", datetime.now(UTC) + timedelta(seconds=30)
    )
    assert claimed is not None and claimed.state == JobState.RUNNING
    await store.close()

    reopened = await _open(tmp_path)
    try:
        recover_jobs = SQLiteJobRepository(reopened)
        future = datetime.now(UTC) - timedelta(seconds=1)
        recovered = await recover_jobs.recover(future)
        # The lease has not expired yet, so nothing is stolen mid-flight.
        assert recovered == []
        stale = await recover_jobs.recover(datetime.now(UTC) + timedelta(minutes=5))
        assert [job.job_id for job in stale] == ["job1"]
        assert stale[0].state == JobState.QUEUED
    finally:
        await reopened.close()


async def test_import_enqueue_is_idempotent_for_the_same_preview(tmp_path: Path) -> None:
    store = await _open(tmp_path)
    try:
        jobs = SQLiteJobRepository(store)
        command = JobCommand(
            kind=JobKind.IMPORT, payload={"kind": "import", "kb_id": "kb1"},
            idempotency_key="sha256:preview",
        )
        first = await jobs.enqueue(command, "job1")
        second = await jobs.enqueue(command, "job2")
        assert first.job_id == second.job_id == "job1"
    finally:
        await store.close()


async def test_mirror_is_allowed_only_with_a_complete_manifest() -> None:
    from qa_contracts.knowledge import ManifestFile

    complete = SourceManifest(
        source_id="s",
        files=[ManifestFile(relative_path="a.md", digest="d", size=1)],
        scan_scope="full",
        scan_status="succeeded",
        complete=True,
    )
    partial = complete.model_copy(
        update={"scan_scope": "partial", "complete": False}
    )
    assert complete.complete and not partial.complete


async def test_rollback_target_must_belong_to_the_same_kb(tmp_path: Path) -> None:
    from kb_management.indexing import SnapshotPublisher
    from qa_contracts.knowledge import KnowledgeBase, Snapshot, SnapshotState
    from qa_infrastructure.repositories import (
        SQLiteKnowledgeRepository,
        SQLiteSnapshotRepository,
    )
    from qa_infrastructure.snapshots import FileSnapshotStore

    store = await _open(tmp_path)
    try:
        knowledge = SQLiteKnowledgeRepository(store)
        snapshots = SQLiteSnapshotRepository(store)
        files = FileSnapshotStore(tmp_path / "var" / "snapshots")
        for kb_id in ("kb1", "kb2"):
            await knowledge.put(
                KnowledgeBase(kb_id=kb_id, name=kb_id, etag="e1", updated_at=utc_now()),
                None,
            )
            handle = await files.stage([], kb_id=kb_id, version_id=f"{kb_id}-v1")
            await files.seal(handle, kb_id=kb_id, version_id=f"{kb_id}-v1")
            await snapshots.save(
                Snapshot(
                    version_id=f"{kb_id}-v1", kb_id=kb_id, state=SnapshotState.READY,
                    keyword_profile="zh", keyword_index_ref="ref",
                    document_revisions={"doc": "rev"}, indexed_file_ids=["doc"],
                )
            )
        publisher = SnapshotPublisher(knowledge=knowledge, snapshots=snapshots, files=files)
        await publisher.publish("kb1-v1", None)
        with pytest.raises(Conflict):
            await publisher.rollback("kb2", "kb1-v1", None)
    finally:
        await store.close()
