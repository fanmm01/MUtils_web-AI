"""Cross-source, cross-batch and delete semantics that must not lose data.

Every case here is a way a *second* operation could silently erase the first
one's result: another source's import, a replay of the same confirmation, two
concurrent upload batches for the same path, or deleting a base that still has
content. Each one must be refused or must preserve the other data.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from kb_management.indexing import ChangePlanner
from qa_contracts.errors import Conflict, NotFound, ValidationFailed
from qa_contracts.knowledge import (
    ManifestFile,
    Source,
    SourceManifest,
    UploadManifest,
)
from qa_infrastructure.sqlite import SQLiteStore


def _write(root: Path, name: str, text: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _manifest(source_id: str, root: Path, names: list[str]) -> SourceManifest:
    return SourceManifest(
        source_id=source_id,
        files=[
            ManifestFile(
                relative_path=name,
                digest=hashlib.sha256((root / name).read_bytes()).hexdigest(),
                size=(root / name).stat().st_size,
            )
            for name in names
        ],
        scan_scope="full",
        scan_status="succeeded",
        complete=True,
    )


class _Splitter:
    def split(self, document, *, kb_id, version_id, revision_id, profile):  # type: ignore[no-untyped-def]
        from qa_contracts.knowledge import Chunk

        return [
            Chunk(
                chunk_id=f"{revision_id}-{index}",
                kb_id=kb_id,
                version_id=version_id,
                revision_id=revision_id,
                content_hash=hashlib.sha256(block.text.encode()).hexdigest(),
                text=block.text,
                locator=block.locator,
                ordinal=index,
            )
            for index, block in enumerate(document.blocks)
        ]


async def _wired(tmp_path: Path, root: Path):
    from kb_management.imports import FileResolver, ImportService
    from kb_management.indexing import IndexBuilder
    from kb_management.parsers import ParserRegistry
    from kb_management.service import KBService
    from kb_management.sources import SourceService
    from qa_contracts.knowledge import CreateKB
    from qa_infrastructure.indexes import BM25Index
    from qa_infrastructure.repositories import (
        SQLiteContentRepository,
        SQLiteImportPreviewRepository,
        SQLiteJobRepository,
        SQLiteKnowledgeRepository,
        SQLiteQARepository,
        SQLiteSnapshotRepository,
        SQLiteSourceRepository,
    )
    from qa_infrastructure.snapshots import FileSnapshotStore

    database = tmp_path / "var" / "qa.sqlite3"
    creating = SQLiteStore(database)
    await creating.migrate("head")
    await creating.close()
    store = SQLiteStore(database)
    await store.open()
    repos = {
        "knowledge": SQLiteKnowledgeRepository(store),
        "sources": SQLiteSourceRepository(store),
        "content": SQLiteContentRepository(store),
        "snapshots": SQLiteSnapshotRepository(store),
        "jobs": SQLiteJobRepository(store),
        "previews": SQLiteImportPreviewRepository(store),
        "qa": SQLiteQARepository(store),
    }
    files = FileSnapshotStore(tmp_path / "var" / "snapshots")
    builder = IndexBuilder(
        knowledge=repos["knowledge"],
        sources=repos["sources"],
        content=repos["content"],
        snapshots=repos["snapshots"],
        files=files,
        parser=ParserRegistry(),
        splitter=_Splitter(),
        keyword_writer=BM25Index(tmp_path / "var" / "indexes"),
        chunk_profile=__import__(
            "qa_contracts.knowledge", fromlist=["ChunkProfile"]
        ).ChunkProfile(target_tokens=200, overlap_tokens=20),
        store=store,
        qa_pairs=repos["qa"],
    )
    imports = ImportService(
        knowledge=repos["knowledge"],
        sources=repos["sources"],
        previews=repos["previews"],
        jobs=repos["jobs"],
        builder=builder,
        files=FileResolver({"src_a": root, "src_b": root}),
        local_roots={"root_a": root, "root_b": root},
        upload_root=tmp_path / "var" / "uploads",
    )
    kb = await KBService(knowledge=repos["knowledge"]).create(CreateKB(name="多来源"))
    for source_id, root_id in (("src_a", "root_a"), ("src_b", "root_b")):
        await repos["sources"].put(
            Source(
                source_id=source_id, kb_id=kb.kb_id, kind="local_root", root_id=root_id,
                display_name=source_id, revision="r1",
            ),
            None,
        )
    bundle = {
        "source_repo": repos["sources"],
        "store": store,
        "kb": kb,
        "root": root,
        "files": files,
        "imports": imports,
        "builder": builder,
        "sources": SourceService(sources=repos["sources"]),
        "knowledge": repos["knowledge"],
        **repos,
    }
    return bundle


async def _import(bundle, source_id: str, names: list[str]):  # type: ignore[no-untyped-def]
    from qa_contracts.knowledge import ImportPreviewRequest, ImportRequest

    root = bundle["root"]
    manifest = _manifest(source_id, root, names)
    preview = await bundle["imports"].preview(
        ImportPreviewRequest(kb_id=bundle["kb"].kb_id, source_id=source_id), manifest
    )
    job = await bundle["imports"].apply(
        ImportRequest(
            kb_id=bundle["kb"].kb_id,
            source_id=source_id,
            expected_preview_hash=preview.preview_hash,
        ),
        manifest,
    )
    return await bundle["imports"].execute(
        job, files=bundle["imports"].file_paths(
            await bundle["sources"].get(source_id), manifest
        )
    )


async def test_source_b_import_keeps_source_a_content(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    root.mkdir()
    _write(root, "a.md", "# 来源 A\n\n来自 A 库的内容。\n")
    _write(root, "b.md", "# 来源 B\n\n来自 B 库的内容。\n")
    bundle = await _wired(tmp_path, root)
    try:
        first = await _import(bundle, "src_a", ["a.md"])
        assert not first.failed, first.reason
        second = await _import(bundle, "src_b", ["b.md"])
        assert not second.failed, second.reason
        texts = [
            chunk.text
            for chunk in await bundle["files"].load_all_chunks(
                bundle["kb"].kb_id, second.snapshot.version_id
            )
        ]
        assert any("来源 A" in text for text in texts), "source B must not drop source A"
        assert any("来源 B" in text for text in texts)
        assert set(second.snapshot.document_revisions) >= set(
            first.snapshot.document_revisions
        )
    finally:
        await bundle["store"].close()


async def test_source_import_keeps_manual_documents_and_qa_pairs(tmp_path: Path) -> None:
    from kb_management.content import ContentService
    from qa_contracts.knowledge import PutDocument, PutQA

    root = tmp_path / "corpus"
    root.mkdir()
    _write(root, "a.md", "源文件内容。\n")
    bundle = await _wired(tmp_path, root)
    try:
        content = ContentService(content=bundle["content"], qa_pairs=bundle["qa"])
        document = await content.put(
            PutDocument(kb_id=bundle["kb"].kb_id, title="手工文档", text="手工录入的正文。")
        )
        pair = await content.put_qa(
            PutQA(kb_id=bundle["kb"].kb_id, question="手工问题", answer="手工答案")
        )
        outcome = await _import(bundle, "src_a", ["a.md"])
        assert not outcome.failed, outcome.reason
        texts = [
            chunk.text
            for chunk in await bundle["files"].load_all_chunks(
                bundle["kb"].kb_id, outcome.snapshot.version_id
            )
        ]
        assert any("源文件内容" in text for text in texts)
        assert any("手工录入" in text for text in texts)
        assert any("手工问题" in text for text in texts)
        detail = await bundle["content"].get(document.document_id, revision_id=None)
        assert detail.document.latest_revision_id
        assert (await content.get_qa(pair.document_id)).question == "手工问题"
    finally:
        await bundle["store"].close()


async def test_same_confirmation_returns_the_same_job(tmp_path: Path) -> None:
    from qa_contracts.knowledge import ImportPreviewRequest, ImportRequest

    root = tmp_path / "corpus"
    root.mkdir()
    _write(root, "a.md", "内容。\n")
    bundle = await _wired(tmp_path, root)
    try:
        manifest = _manifest("src_a", root, ["a.md"])
        preview = await bundle["imports"].preview(
            ImportPreviewRequest(kb_id=bundle["kb"].kb_id, source_id="src_a"), manifest
        )
        request = ImportRequest(
            kb_id=bundle["kb"].kb_id,
            source_id="src_a",
            expected_preview_hash=preview.preview_hash,
        )
        first = await bundle["imports"].apply(request, manifest)
        replay = await bundle["imports"].apply(request, manifest)
        assert replay.job_id == first.job_id, "a confirmed preview is idempotent"
        changed = await bundle["imports"].preview(
            ImportPreviewRequest(kb_id=bundle["kb"].kb_id, source_id="src_a"), manifest
        )
        # A fresh preview of unchanged files has the same content hash by design;
        # a genuinely different preview must still produce a different job.
        _write(root, "a.md", "内容变了。\n")
        changed_manifest = _manifest("src_a", root, ["a.md"])
        changed_preview = await bundle["imports"].preview(
            ImportPreviewRequest(kb_id=bundle["kb"].kb_id, source_id="src_a"),
            changed_manifest,
        )
        assert changed_preview.preview_hash != preview.preview_hash
        new_job = await bundle["imports"].apply(
            ImportRequest(
                kb_id=bundle["kb"].kb_id,
                source_id="src_a",
                expected_preview_hash=changed_preview.preview_hash,
            ),
            changed_manifest,
        )
        assert new_job.job_id != first.job_id
        del changed
    finally:
        await bundle["store"].close()


async def test_two_upload_batches_for_the_same_path_stay_isolated(tmp_path: Path) -> None:
    import io

    from kb_management.sources import UploadSource
    from qa_infrastructure.repositories import SQLiteUploadRepository

    root = tmp_path / "corpus"
    root.mkdir()
    bundle = await _wired(tmp_path, root)
    uploads = SQLiteUploadRepository(bundle["store"])

    async def source_service() -> UploadSource:
        return UploadSource(
            blobs=object(),
            uploads=uploads,
            sources=bundle["sources"],
            upload_root=tmp_path / "var" / "uploads",
        )

    try:
        first_source = await source_service()
        second_source = await source_service()
        for source_id in ("up_1", "up_2"):
            await bundle["source_repo"].put(
                Source(
                    source_id=source_id, kb_id=bundle["kb"].kb_id, kind="upload",
                    display_name=source_id, revision="r1",
                ),
                None,
            )
        payloads = {"up_1": b"first", "up_2": b"second"}
        batches = {}
        for source_id, payload in payloads.items():
            digest = hashlib.sha256(payload).hexdigest()
            batch = await (first_source if source_id == "up_1" else second_source).begin(
                UploadManifest.model_validate(
                    {
                        "source_id": source_id,
                        "files": [
                            {"relative_path": "shared.md", "digest": digest,
                             "size": len(payload)}
                        ],
                    }
                )
            )
            batches[source_id] = batch.batch_id
            await (first_source if source_id == "up_1" else second_source).write(
                batch.batch_id, "shared.md", io.BytesIO(payload)
            )
        for source_id, payload in payloads.items():
            manifest = await (
                first_source if source_id == "up_1" else second_source
            ).finish(batches[source_id])
            assert manifest.files[0].digest == hashlib.sha256(payload).hexdigest()
            stored = (
                tmp_path / "var" / "uploads"
                / hashlib.sha256(source_id.encode()).hexdigest()
                / hashlib.sha256(hashlib.sha256(payload).hexdigest().encode()).hexdigest()
                / "shared.md"
            )
            assert stored.read_bytes() == payload
    finally:
        await bundle["store"].close()


async def test_batch_of_one_source_cannot_overwrite_another_sources_bytes(
    tmp_path: Path,
) -> None:
    import io

    from kb_management.sources import UploadSource
    from qa_infrastructure.repositories import SQLiteUploadRepository

    root = tmp_path / "corpus"
    root.mkdir()
    bundle = await _wired(tmp_path, root)
    uploads = SQLiteUploadRepository(bundle["store"])
    source = UploadSource(
        blobs=object(),
        uploads=uploads,
        sources=bundle["sources"],
        upload_root=tmp_path / "var" / "uploads",
    )
    try:
        await bundle["source_repo"].put(
            Source(
                source_id="up_x", kb_id=bundle["kb"].kb_id, kind="upload",
                display_name="up", revision="r1",
            ),
            None,
        )
        digest_a = hashlib.sha256(b"aaa").hexdigest()
        batch = await source.begin(
            UploadManifest.model_validate(
                {
                    "source_id": "up_x",
                    "files": [
                        {"relative_path": "x.md", "digest": digest_a, "size": 3}
                    ],
                }
            )
        )
        # A mismatching body for a claimed digest must not be stored at all.
        with pytest.raises(ValidationFailed):
            await source.write(batch.batch_id, "x.md", io.BytesIO(b"bbb"))
        manifest = await source.finish(batch.batch_id)
        assert manifest.scan_status == "failed"
        assert manifest.files == []
    finally:
        await bundle["store"].close()


async def test_kb_delete_refuses_a_base_with_sources_or_versions(tmp_path: Path) -> None:
    from kb_management.service import KBService
    from qa_contracts.knowledge import CreateKB

    database = tmp_path / "var" / "qa.sqlite3"
    creating = SQLiteStore(database)
    await creating.migrate("head")
    await creating.close()
    store = SQLiteStore(database)
    await store.open()
    try:
        from qa_infrastructure.repositories import (
            SQLiteKnowledgeRepository,
            SQLiteSourceRepository,
        )

        knowledge = SQLiteKnowledgeRepository(store)
        sources = SQLiteSourceRepository(store)
        service = KBService(knowledge=knowledge, sources=sources)
        kb = await service.create(CreateKB(name="待删"))
        # An empty base may be deleted.
        empty = await service.create(CreateKB(name="空库"))
        await service.delete(empty.kb_id, empty.etag)
        await sources.put(
            Source(
                source_id="src_del", kb_id=kb.kb_id, kind="upload",
                display_name="d", revision="r1",
            ),
            None,
        )
        with pytest.raises(Conflict):
            await service.delete(kb.kb_id, kb.etag)
        assert (await knowledge.get(kb.kb_id)).kb_id == kb.kb_id

        await sources.remove("src_del")
        await service.delete(kb.kb_id, kb.etag)
        with pytest.raises(NotFound):
            await knowledge.get(kb.kb_id)
    finally:
        await store.close()


def test_change_planner_keeps_unchanged_when_diffing_second_source() -> None:
    from qa_contracts.knowledge import ManifestFile

    first = SourceManifest(
        source_id="a",
        files=[ManifestFile(relative_path="a.md", digest="1", size=1)],
        scan_scope="full",
        scan_status="succeeded",
        complete=True,
    )
    second = SourceManifest(
        source_id="b",
        files=[ManifestFile(relative_path="b.md", digest="2", size=1)],
        scan_scope="full",
        scan_status="succeeded",
        complete=True,
    )
    change = ChangePlanner.diff(first, second, mode="mirror")
    assert change.added == ["b.md"]
    assert change.removed == ["a.md"], "mirror only removes within the same source baseline"
    assert ChangePlanner.diff(None, second, mode="mirror").removed == []




async def test_editing_an_imported_document_keeps_its_source_identity(
    tmp_path: Path,
) -> None:
    """An edit must not orphan the source path, or the next import duplicates it."""
    root = tmp_path / "corpus"
    root.mkdir()
    _write(root, "a.md", "# 标题\n\n源文件正文。\n")
    bundle = await _wired(tmp_path, root)
    try:
        first = await _import(bundle, "src_a", ["a.md"])
        assert not first.failed, first.reason
        document_id = next(iter(first.snapshot.document_revisions))
        detail = await bundle["content"].get(document_id)
        assert detail.revision.source_id == "src_a"
        assert detail.revision.relative_path == "a.md"

        from kb_management.content import ContentService
        from qa_contracts.knowledge import PutDocument

        content = ContentService(content=bundle["content"], qa_pairs=bundle["qa"])
        await content.put(
            PutDocument(
                kb_id=bundle["kb"].kb_id,
                title="标题",
                text="手工润色后的正文。",
                expected_revision_id=detail.document.latest_revision_id,
            ),
            document_id=document_id,
        )
        edited = await bundle["content"].get(document_id)
        assert edited.revision.source_id == "src_a", (
            "an edit must preserve the source identity so imports can match it"
        )
        assert edited.revision.relative_path == "a.md"

        _write(root, "a.md", "# 标题\n\n源文件被再次修改。\n")
        second = await _import(bundle, "src_a", ["a.md"])
        assert not second.failed, second.reason
        assert document_id in second.snapshot.document_revisions, (
            "the imported file must update the existing document, not create another"
        )
        documents = await bundle["content"].list(bundle["kb"].kb_id, 50)
        assert [item.document_id for item in documents.items] == [document_id]
        latest = await bundle["content"].latest_revision(document_id)
        assert "源文件被再次修改" in latest.normalized_text
    finally:
        await bundle["store"].close()


async def test_stale_preview_after_another_import_conflicts(tmp_path: Path) -> None:
    from qa_contracts.knowledge import ImportPreviewRequest, ImportRequest

    root = tmp_path / "corpus"
    root.mkdir()
    _write(root, "a.md", "第一版。\n")
    bundle = await _wired(tmp_path, root)
    try:
        manifest = _manifest("src_a", root, ["a.md"])
        preview = await bundle["imports"].preview(
            ImportPreviewRequest(kb_id=bundle["kb"].kb_id, source_id="src_a"), manifest
        )
        applied = await bundle["imports"].apply(
            ImportRequest(
                kb_id=bundle["kb"].kb_id,
                source_id="src_a",
                expected_preview_hash=preview.preview_hash,
            ),
            manifest,
        )
        await bundle["imports"].execute(
            applied, files=bundle["imports"].file_paths(
                await bundle["sources"].get("src_a"), manifest
            )
        )
        # The baseline moved; the old preview is no longer valid evidence.
        _write(root, "a.md", "第二版。\n")
        with pytest.raises(Conflict):
            await bundle["imports"].apply(
                ImportRequest(
                    kb_id=bundle["kb"].kb_id,
                    source_id="src_a",
                    expected_preview_hash=preview.preview_hash,
                ),
                _manifest("src_a", root, ["a.md"]),
            )
    finally:
        await bundle["store"].close()


async def test_upload_finish_is_idempotent(tmp_path: Path) -> None:
    import io

    from kb_management.sources import UploadSource
    from qa_infrastructure.repositories import SQLiteUploadRepository

    root = tmp_path / "corpus"
    root.mkdir()
    bundle = await _wired(tmp_path, root)
    source = UploadSource(
        blobs=object(),
        uploads=SQLiteUploadRepository(bundle["store"]),
        sources=bundle["sources"],
        upload_root=tmp_path / "var" / "uploads",
    )
    try:
        await bundle["source_repo"].put(
            Source(
                source_id="up_idem", kb_id=bundle["kb"].kb_id, kind="upload",
                display_name="u", revision="r1",
            ),
            None,
        )
        payload = b"payload"
        batch = await source.begin(
            UploadManifest.model_validate(
                {
                    "source_id": "up_idem",
                    "files": [{
                        "relative_path": "p.md",
                        "digest": hashlib.sha256(payload).hexdigest(),
                        "size": len(payload),
                    }],
                }
            )
        )
        await source.write(batch.batch_id, "p.md", io.BytesIO(payload))
        first = await source.finish(batch.batch_id)
        second = await source.finish(batch.batch_id)
        assert first == second
        assert second.complete is True
    finally:
        await bundle["store"].close()
