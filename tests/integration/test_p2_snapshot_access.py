"""Published reads must reject draft versions and corrupted sealed files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from qa_contracts.errors import NotFound, ResourceGone
from qa_contracts.knowledge import Chunk, KnowledgeBase, Locator, Revision, Snapshot, SnapshotState
from qa_contracts.operations import AccessScope
from qa_contracts.selection import KBTarget, PinnedKBTarget
from qa_infrastructure.repositories import SQLiteKnowledgeRepository, SQLiteSnapshotRepository
from qa_infrastructure.snapshots import FileSnapshotStore, PublishedSnapshotReader
from qa_infrastructure.sqlite import SQLiteStore


@pytest.fixture
async def sealed(tmp_path: Path):
    store = SQLiteStore(tmp_path / "data" / "qa.sqlite3")
    await store.migrate("head")
    await store.open()
    knowledge = SQLiteKnowledgeRepository(store)
    snapshots = SQLiteSnapshotRepository(store)
    files = FileSnapshotStore(tmp_path / "data" / "snapshots")
    await knowledge.create(KnowledgeBase(kb_id="kb1", name="base", etag="e1"))
    revision = Revision(revision_id="rev1", document_id="doc1", normalized_text="example")
    chunk = Chunk(
        chunk_id="chunk1", kb_id="kb1", version_id="ver1", revision_id="rev1",
        text="example", content_hash=hashlib.sha256(b"example").hexdigest(),
        locator=Locator(kind="text_lines", start_line=1, end_line=1), ordinal=0,
    )
    await store.execute(
        "INSERT INTO documents (document_id,kb_id,title,latest_revision_id,updated_at)"
        " VALUES ('doc1','kb1','example','rev1','2026-11-06T00:00:00Z')"
    )
    await store.execute(
        "INSERT INTO revisions (revision_id,document_id,normalized_text,created_at)"
        " VALUES ('rev1','doc1','example','2026-11-06T00:00:00Z')"
    )
    handle = await files.stage(["example.txt"], kb_id="kb1", version_id="ver1")
    await files.append_chunks(handle, [chunk])
    await files.write_revision(handle, revision)
    await files.seal(handle, kb_id="kb1", version_id="ver1")
    snapshot = Snapshot(
        version_id="ver1", kb_id="kb1", state=SnapshotState.READY,
        keyword_profile="zh", keyword_index_ref="idx", document_revisions={"doc1": "rev1"},
        indexed_file_ids=["example.txt"],
    )
    await snapshots.save(snapshot)
    reader = PublishedSnapshotReader(
        store=store, files=files, knowledge=knowledge, snapshots=snapshots
    )
    try:
        yield files, snapshots, reader, snapshot
    finally:
        await store.close()


async def test_ready_snapshot_is_not_visible_to_question_readers(sealed) -> None:
    files, snapshots, reader, snapshot = sealed
    access = AccessScope(principal_id="p", kb_ids=["kb1"])
    target = PinnedKBTarget(kb_id="kb1", version_id="ver1")
    with pytest.raises(NotFound):
        await reader.resolve("kb1", "ver1", access)
    with pytest.raises(NotFound):
        await reader.resolve_many([KBTarget(kb_id="kb1", version_id="ver1")], access)
    with pytest.raises(NotFound):
        await reader.search_scope(target, access)
    with pytest.raises(NotFound):
        await reader.load_chunks(target, ["chunk1"], access)
    with pytest.raises(ResourceGone):
        await reader.load_revision("rev1", access)
    assert await files.verify("kb1", "ver1")
    assert (await snapshots.get("ver1")).state == snapshot.state


async def test_manifest_tampering_rejects_all_read_paths(sealed) -> None:
    files, snapshots, reader, snapshot = sealed
    access = AccessScope(principal_id="p", kb_ids=["kb1"])
    target = PinnedKBTarget(kb_id="kb1", version_id="ver1")
    await snapshots.save(snapshot.model_copy(update={"state": SnapshotState.PUBLISHED}))
    assert await files.verify("kb1", "ver1")
    assert len(await reader.load_chunks(target, ["chunk1"], access)) == 1
    assert (await reader.load_revision("rev1", access)).normalized_text == "example"
    manifest = files.version_dir("kb1", "ver1") / "snapshot.json"
    original = manifest.read_text(encoding="utf-8")
    manifest.write_text("{}", encoding="utf-8")
    assert not await files.verify("kb1", "ver1")
    with pytest.raises(ResourceGone):
        await reader.resolve("kb1", "ver1", access)
    with pytest.raises(ResourceGone):
        await files.load_all_chunks("kb1", "ver1")
    with pytest.raises(ResourceGone):
        await reader.load_chunks(target, ["chunk1"], access)
    with pytest.raises(ResourceGone):
        await reader.load_revision("rev1", access)

    payload = json.loads(original)
    payload["kb_id"] = "another-base"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    assert not await files.verify("kb1", "ver1")
    manifest.write_text(original, encoding="utf-8")
    (files.version_dir("kb1", "ver1") / "chunks.jsonl").write_text("", encoding="utf-8")
    assert not await files.verify("kb1", "ver1")
