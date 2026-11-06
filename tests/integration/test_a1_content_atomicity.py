"""A failed synchronous rebuild must not leave a successful-looking content edit."""

from __future__ import annotations

import pytest

from kb_management.content import ContentService
from qa_contracts.errors import NotFound, ProviderUnavailable
from qa_contracts.knowledge import PutDocument, PutQA


class FailingRebuild:
    async def request_build(self, kb_id: str, *, reason: str) -> str:
        raise RuntimeError("index writer failed")


class EmptyRebuild:
    async def request_build(self, kb_id: str, *, reason: str) -> None:
        return None


def _service(store, content, qa_pairs, builds=None) -> ContentService:
    return ContentService(content=content, qa_pairs=qa_pairs, builds=builds, store=store)


async def test_failed_create_rolls_back_document_and_revision(store, content, qa_pairs) -> None:
    service = _service(store, content, qa_pairs, FailingRebuild())
    with pytest.raises(RuntimeError, match="index writer failed"):
        await service.put(PutDocument(kb_id="kb1", title="manual", text="unpublished"))
    assert (await content.list("kb1")).items == []
    assert await store.fetchall("SELECT revision_id FROM revisions") == []


async def test_failed_edit_restores_previous_revision(store, content, qa_pairs) -> None:
    original = _service(store, content, qa_pairs)
    receipt = await original.put(PutDocument(kb_id="kb1", title="manual", text="original"))
    before = await content.get(receipt.document_id)
    with pytest.raises(RuntimeError, match="index writer failed"):
        await _service(store, content, qa_pairs, FailingRebuild()).put(
            PutDocument(
                kb_id="kb1", title="manual", text="new content",
                expected_revision_id=before.revision.revision_id,
            ),
            document_id=receipt.document_id,
        )
    after = await content.get(receipt.document_id)
    assert after.revision.revision_id == before.revision.revision_id
    assert after.revision.normalized_text == "original"
    revisions = await store.fetchall(
        "SELECT revision_id FROM revisions WHERE document_id = ?", (receipt.document_id,)
    )
    assert [row["revision_id"] for row in revisions] == [before.revision.revision_id]


async def test_failed_delete_keeps_document_visible(store, content, qa_pairs) -> None:
    original = _service(store, content, qa_pairs)
    receipt = await original.put(PutDocument(kb_id="kb1", title="manual", text="keep"))
    revision = (await content.get(receipt.document_id)).revision.revision_id
    with pytest.raises(RuntimeError, match="index writer failed"):
        await _service(store, content, qa_pairs, FailingRebuild()).delete(
            receipt.document_id, revision
        )
    assert [item.document_id for item in (await content.list("kb1")).items] == [
        receipt.document_id
    ]


async def test_failed_qa_create_rolls_back_both_tables(store, content, qa_pairs) -> None:
    with pytest.raises(RuntimeError, match="index writer failed"):
        await _service(store, content, qa_pairs, FailingRebuild()).put_qa(
            PutQA(kb_id="kb1", question="question", answer="answer")
        )
    assert (await qa_pairs.list("kb1")).items == []
    assert (await content.list("kb1")).items == []
    assert await store.fetchall("SELECT revision_id FROM revisions") == []


async def test_failed_qa_edit_and_delete_restore_pair(store, content, qa_pairs) -> None:
    original = _service(store, content, qa_pairs)
    receipt = await original.put_qa(PutQA(kb_id="kb1", question="q", answer="old"))
    before = await qa_pairs.get(receipt.document_id)
    failure = _service(store, content, qa_pairs, FailingRebuild())
    with pytest.raises(RuntimeError, match="index writer failed"):
        await failure.put_qa(
            PutQA(
                kb_id="kb1", question="q", answer="new",
                expected_revision_id=before.revision_id,
            ),
            qa_id=receipt.document_id,
        )
    assert (await qa_pairs.get(receipt.document_id)).answer == "old"
    assert (await content.get(receipt.document_id)).revision.revision_id == before.revision_id
    with pytest.raises(RuntimeError, match="index writer failed"):
        await failure.delete_qa(receipt.document_id, before.revision_id)
    assert (await qa_pairs.get(receipt.document_id)).deleted is False
    assert (await content.get(receipt.document_id)).document.deleted is False


async def test_real_empty_rebuild_leaves_no_document_or_snapshot(
    store, content, qa_pairs, knowledge, sources, snapshots, snapshot_files, tmp_path
) -> None:
    from kb_management.indexing import BuildRequest, IndexBuilder
    from kb_management.parsers import ParserRegistry
    from kb_management.service import KBService
    from qa_contracts.knowledge import ChunkProfile, CreateKB
    from qa_infrastructure.indexes import BM25Index

    class EmptySplitter:
        def split(self, document, *, kb_id, version_id, revision_id, profile):
            return []

    kb = await KBService(knowledge=knowledge).create(CreateKB(name="empty"))
    builder = IndexBuilder(
        knowledge=knowledge, sources=sources, content=content, snapshots=snapshots,
        files=snapshot_files, parser=ParserRegistry(), splitter=EmptySplitter(),
        keyword_writer=BM25Index(tmp_path / "indexes"),
        chunk_profile=ChunkProfile(target_tokens=80, overlap_tokens=10), store=store,
        qa_pairs=qa_pairs,
    )

    class RealRebuild:
        async def request_build(self, kb_id: str, *, reason: str) -> str | None:
            outcome = await builder.build(BuildRequest(kb_id=kb_id))
            return outcome.snapshot.version_id if outcome.snapshot is not None else None

    with pytest.raises(ProviderUnavailable, match="snapshot could not be built"):
        await _service(store, content, qa_pairs, RealRebuild()).put(
            PutDocument(kb_id=kb.kb_id, title="empty", text=""),
        )
    assert (await content.list(kb.kb_id)).items == []
    assert await snapshots.list(kb.kb_id) == []
    assert await store.fetchall("SELECT revision_id FROM revisions") == []


async def test_no_snapshot_is_an_error_not_a_successful_write(store, content, qa_pairs) -> None:
    service = _service(store, content, qa_pairs, EmptyRebuild())
    with pytest.raises(ProviderUnavailable, match="snapshot could not be built"):
        await service.put(PutDocument(kb_id="kb1", title="manual", text="missing snapshot"))
    assert (await content.list("kb1")).items == []
    with pytest.raises(NotFound):
        await content.get("doc_missing")
