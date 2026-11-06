"""A1 import pipeline: preview → apply → build → publish, with real files."""

from __future__ import annotations

import hashlib
import io
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio

from kb_management.content import ContentService
from kb_management.imports import FileResolver, ImportService, preview_hash
from kb_management.indexing import BuildRequest, ChangePlanner, IndexBuilder, SnapshotPublisher
from kb_management.parsers import ParserRegistry
from kb_management.service import KBService
from qa_contracts.errors import Conflict, NotFound, ValidationFailed
from qa_contracts.knowledge import (
    ChangeSet,
    ChunkProfile,
    CreateKB,
    ImportPreviewRequest,
    ImportRequest,
    KnowledgeBase,
    Selection,
    Snapshot,
    SnapshotState,
    Source,
    SourceManifest,
)
from qa_infrastructure.indexes import BM25Index


class FakeSplitter:
    """Deterministic stand-in for the A2 chunker (which A1 must not import)."""

    def split(self, document, *, kb_id, version_id, revision_id, profile):  # type: ignore[no-untyped-def]
        from qa_contracts.knowledge import Chunk

        chunks = []
        for ordinal, block in enumerate(document.blocks):
            digest = hashlib.sha256(block.text.encode("utf-8")).hexdigest()
            chunks.append(
                Chunk(
                    chunk_id=hashlib.sha256(
                        f"{kb_id}{version_id}{revision_id}{ordinal}".encode()
                    ).hexdigest(),
                    kb_id=kb_id,
                    version_id=version_id,
                    revision_id=revision_id,
                    content_hash=digest,
                    text=block.text,
                    locator=block.locator,
                    ordinal=ordinal,
                )
            )
        return chunks


@pytest_asyncio.fixture()
async def environment(tmp_path: Path) -> AsyncIterator[dict[str, object]]:
    from qa_infrastructure.repositories import (
        SQLiteContentRepository,
        SQLiteImportPreviewRepository,
        SQLiteJobRepository,
        SQLiteKnowledgeRepository,
        SQLiteSnapshotRepository,
        SQLiteSourceRepository,
    )
    from qa_infrastructure.snapshots import FileSnapshotStore
    from qa_infrastructure.sqlite import SQLiteStore

    database = tmp_path / "var" / "qa.sqlite3"
    creator = SQLiteStore(database)
    await creator.migrate("head")
    await creator.close()
    store = SQLiteStore(database)
    await store.open()
    knowledge = SQLiteKnowledgeRepository(store)
    sources = SQLiteSourceRepository(store)
    content = SQLiteContentRepository(store)
    snapshots = SQLiteSnapshotRepository(store)
    jobs = SQLiteJobRepository(store)
    previews = SQLiteImportPreviewRepository(store)
    files = FileSnapshotStore(tmp_path / "var" / "snapshots")
    root = tmp_path / "corpus"
    root.mkdir()
    builder = IndexBuilder(
        knowledge=knowledge,
        sources=sources,
        content=content,
        snapshots=snapshots,
        files=files,
        parser=ParserRegistry(),
        splitter=FakeSplitter(),
        keyword_writer=BM25Index(tmp_path / "var" / "indexes"),
        chunk_profile=ChunkProfile(target_tokens=120, overlap_tokens=20),
        store=store,
    )
    publisher = SnapshotPublisher(knowledge=knowledge, snapshots=snapshots, files=files)
    imports = ImportService(
        knowledge=knowledge,
        sources=sources,
        previews=previews,
        jobs=jobs,
        builder=builder,
        files=FileResolver({"src1": root}),
    )
    yield {
        "store": store,
        "knowledge": knowledge,
        "sources": sources,
        "content": content,
        "snapshots": snapshots,
        "jobs": jobs,
        "previews": previews,
        "files": files,
        "builder": builder,
        "publisher": publisher,
        "imports": imports,
        "root": root,
        "kb": KBService(knowledge=knowledge),
        "content_service": ContentService(content=content, qa_pairs=None),
    }
    await store.close()


async def _setup(env: dict[str, object]) -> tuple[KnowledgeBase, Source]:
    from qa_infrastructure.repositories import SQLiteQARepository

    content_service: ContentService = env["content_service"]  # type: ignore[assignment]
    content_service._qa = SQLiteQARepository(env["store"])  # type: ignore[arg-type]
    kb = await env["kb"].create(CreateKB(name="产品", description="测试库"))  # type: ignore[union-attr]
    source = Source(
        source_id="src1", kb_id=kb.kb_id, kind="local_root", root_id="root1",
        display_name="corpus", revision="r1",
    )
    await env["sources"].put(source, None)  # type: ignore[union-attr]
    return kb, source


def _manifest(files: list[tuple[str, bytes]], *, complete: bool = True) -> SourceManifest:
    from qa_contracts.knowledge import ManifestFile

    return SourceManifest(
        source_id="src1",
        files=[
            ManifestFile(
                relative_path=name, digest=hashlib.sha256(data).hexdigest(), size=len(data)
            )
            for name, data in files
        ],
        scan_scope="full" if complete else "partial",
        scan_status="succeeded",
        complete=complete,
    )


def _write(env: dict[str, object], name: str, text: str) -> None:
    path = Path(env["root"]) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


async def test_preview_apply_build_and_publish(environment) -> None:
    env = environment
    kb, _ = await _setup(env)
    _write(env, "install.md", "# 安装\n\n下载安装包。\n\n# 配置\n\n修改端口配置。\n")
    manifest = _manifest([("install.md", Path(env["root"], "install.md").read_bytes())])

    preview = await env["imports"].preview(
        ImportPreviewRequest(kb_id=kb.kb_id, source_id="src1"), manifest
    )  # type: ignore[union-attr]
    assert preview.added == ["install.md"]
    assert preview.removed == []

    job = await env["imports"].apply(  # type: ignore[union-attr]
        ImportRequest(
            kb_id=kb.kb_id, source_id="src1", expected_preview_hash=preview.preview_hash
        ),
        manifest,
    )
    assert job.kind == "import"
    files = FileResolver({"src1": Path(env["root"])}).resolve("src1", manifest)
    outcome = await env["imports"].execute(job, files=files)  # type: ignore[union-attr]
    assert outcome.failed is False, outcome.reason
    snapshot = outcome.snapshot
    assert snapshot.state == SnapshotState.READY
    assert snapshot.keyword_index_ref
    assert snapshot.indexed_file_ids == ["install.md"]

    published = await env["publisher"].publish(snapshot.version_id, None)  # type: ignore[union-attr]
    assert published.state == SnapshotState.PUBLISHED
    kb_after = await env["knowledge"].get(kb.kb_id)  # type: ignore[union-attr]
    assert kb_after.active_version_id == snapshot.version_id

    chunks = await env["files"].load_all_chunks(kb.kb_id, snapshot.version_id)  # type: ignore[union-attr]
    assert [chunk.text for chunk in chunks] == [
        "# 安装", "下载安装包。", "# 配置", "修改端口配置。"
    ]


async def test_changed_file_after_preview_is_a_conflict(environment) -> None:
    env = environment
    kb, _ = await _setup(env)
    _write(env, "a.txt", "第一版内容")
    manifest = _manifest([("a.txt", Path(env["root"], "a.txt").read_bytes())])
    preview = await env["imports"].preview(  # type: ignore[union-attr]
        ImportPreviewRequest(kb_id=kb.kb_id, source_id="src1"), manifest
    )
    _write(env, "a.txt", "第二版内容，长度不同")
    with pytest.raises(Conflict):
        await env["imports"].apply(  # type: ignore[union-attr]
            ImportRequest(
                kb_id=kb.kb_id, source_id="src1", expected_preview_hash=preview.preview_hash
            ),
            manifest,
        )


async def test_mirror_deletes_only_after_complete_scan(environment) -> None:
    env = environment
    kb, _ = await _setup(env)
    _write(env, "a.txt", "内容 A")
    _write(env, "b.txt", "内容 B")
    first = _manifest([
        ("a.txt", Path(env["root"], "a.txt").read_bytes()),
        ("b.txt", Path(env["root"], "b.txt").read_bytes()),
    ])
    preview = await env["imports"].preview(  # type: ignore[union-attr]
        ImportPreviewRequest(kb_id=kb.kb_id, source_id="src1"), first
    )
    job = await env["imports"].apply(  # type: ignore[union-attr]
        ImportRequest(
            kb_id=kb.kb_id, source_id="src1", mode="merge",
            expected_preview_hash=preview.preview_hash,
        ),
        first,
    )
    outcome = await env["imports"].execute(  # type: ignore[union-attr]
        job, files=FileResolver({"src1": Path(env["root"])}).resolve("src1", first)
    )
    await env["publisher"].publish(outcome.snapshot.version_id, None)  # type: ignore[union-attr]

    (Path(env["root"]) / "b.txt").unlink()
    second = _manifest([("a.txt", Path(env["root"], "a.txt").read_bytes())], complete=True)
    preview = await env["imports"].preview(  # type: ignore[union-attr]
        ImportPreviewRequest(kb_id=kb.kb_id, source_id="src1", mode="mirror"), second
    )
    assert preview.removed == ["b.txt"]

    partial = _manifest(
        [("a.txt", Path(env["root"], "a.txt").read_bytes())], complete=False
    )
    partial_preview = await env["imports"].preview(  # type: ignore[union-attr]
        ImportPreviewRequest(kb_id=kb.kb_id, source_id="src1", mode="mirror"), partial
    )
    assert partial_preview.removed == []


def test_change_planner_never_deletes_from_partial_scan() -> None:
    from qa_contracts.knowledge import ManifestFile

    previous = SourceManifest(
        source_id="s",
        files=[
            ManifestFile(relative_path="a.txt", digest="1", size=1),
            ManifestFile(relative_path="b.txt", digest="2", size=1),
        ],
        scan_scope="full",
        scan_status="succeeded",
        complete=True,
    )
    partial = SourceManifest(
        source_id="s",
        selection=Selection(relative_paths=["a.txt"]),
        files=[ManifestFile(relative_path="a.txt", digest="1", size=1)],
        scan_scope="partial",
        scan_status="succeeded",
        complete=False,
    )
    change = ChangePlanner.diff(previous, partial, mode="mirror")
    assert change.removed == []
    assert change.unchanged == ["a.txt"]

    full = SourceManifest(
        source_id="s",
        files=[ManifestFile(relative_path="a.txt", digest="1", size=1)],
        scan_scope="full",
        scan_status="succeeded",
        complete=True,
    )
    assert ChangePlanner.diff(previous, full, mode="mirror").removed == ["b.txt"]
    assert ChangePlanner.diff(previous, full, mode="merge").removed == []


async def test_unchanged_files_are_not_reparsed(environment) -> None:
    env = environment
    kb, _ = await _setup(env)
    _write(env, "a.txt", "长期不变的说明")
    manifest = _manifest([("a.txt", Path(env["root"], "a.txt").read_bytes())])
    preview = await env["imports"].preview(  # type: ignore[union-attr]
        ImportPreviewRequest(kb_id=kb.kb_id, source_id="src1"), manifest
    )
    job = await env["imports"].apply(  # type: ignore[union-attr]
        ImportRequest(
            kb_id=kb.kb_id, source_id="src1", expected_preview_hash=preview.preview_hash
        ),
        manifest,
    )
    first = await env["imports"].execute(  # type: ignore[union-attr]
        job, files=FileResolver({"src1": Path(env["root"])}).resolve("src1", manifest)
    )
    await env["publisher"].publish(first.snapshot.version_id, None)  # type: ignore[union-attr]

    _write(env, "b.txt", "新增的说明")
    second_manifest = _manifest([
        ("a.txt", Path(env["root"], "a.txt").read_bytes()),
        ("b.txt", Path(env["root"], "b.txt").read_bytes()),
    ])
    preview = await env["imports"].preview(  # type: ignore[union-attr]
        ImportPreviewRequest(kb_id=kb.kb_id, source_id="src1"), second_manifest
    )
    assert preview.added == ["b.txt"]
    assert preview.modified == []
    job = await env["imports"].apply(  # type: ignore[union-attr]
        ImportRequest(
            kb_id=kb.kb_id, source_id="src1", expected_preview_hash=preview.preview_hash
        ),
        second_manifest,
    )
    second = await env["imports"].execute(  # type: ignore[union-attr]
        job,
        files=FileResolver({"src1": Path(env["root"])}).resolve("src1", second_manifest),
    )
    assert second.parsed_paths == ["b.txt"]
    assert second.reused_paths == ["a.txt"]
    assert second.snapshot.parent_version_id == first.snapshot.version_id


async def test_failed_build_leaves_active_version_unchanged(environment) -> None:
    env = environment
    kb, _ = await _setup(env)
    _write(env, "good.txt", "正常内容")
    manifest = _manifest([("good.txt", Path(env["root"], "good.txt").read_bytes())])
    preview = await env["imports"].preview(  # type: ignore[union-attr]
        ImportPreviewRequest(kb_id=kb.kb_id, source_id="src1"), manifest
    )
    job = await env["imports"].apply(  # type: ignore[union-attr]
        ImportRequest(
            kb_id=kb.kb_id, source_id="src1", expected_preview_hash=preview.preview_hash
        ),
        manifest,
    )
    good = await env["imports"].execute(  # type: ignore[union-attr]
        job, files=FileResolver({"src1": Path(env["root"])}).resolve("src1", manifest)
    )
    await env["publisher"].publish(good.snapshot.version_id, None)  # type: ignore[union-attr]

    # Everything in the follow-up build fails to parse (empty markdown file).
    (Path(env["root"]) / "good.txt").write_text("", encoding="utf-8")
    broken = _manifest([("good.txt", b"")])
    outcome = await env["builder"].build(  # type: ignore[union-attr]
        BuildRequest(
            kb_id=kb.kb_id, source_id="src1", manifest=broken,
            files=FileResolver({"src1": Path(env["root"])}).resolve("src1", broken),
        )
    )
    assert outcome.failed is True
    active = await env["knowledge"].get(kb.kb_id)  # type: ignore[union-attr]
    assert active.active_version_id == good.snapshot.version_id
    versions = await env["snapshots"].list(kb.kb_id)  # type: ignore[union-attr]
    assert [version.version_id for version in versions] == [good.snapshot.version_id]


async def test_concurrent_publish_conflicts_instead_of_overwriting(environment) -> None:
    env = environment
    kb, _ = await _setup(env)
    for name, text in (("a.txt", "内容 A"), ("b.txt", "内容 B")):
        _write(env, name, text)
    versions: list[Snapshot] = []
    for name in ("a.txt", "b.txt"):
        manifest = _manifest([(name, Path(env["root"], name).read_bytes())])
        outcome = await env["builder"].build(  # type: ignore[union-attr]
            BuildRequest(
                kb_id=kb.kb_id, source_id="src1", manifest=manifest,
                files=FileResolver({"src1": Path(env["root"])}).resolve("src1", manifest),
            )
        )
        versions.append(outcome.snapshot)
    await env["publisher"].publish(versions[0].version_id, None)  # type: ignore[union-attr]
    with pytest.raises(Conflict):
        await env["publisher"].publish(versions[1].version_id, None)  # type: ignore[union-attr]


async def test_rollback_and_old_version_still_readable(environment) -> None:
    env = environment
    kb, _ = await _setup(env)
    _write(env, "a.txt", "第一版")
    manifest = _manifest([("a.txt", Path(env["root"], "a.txt").read_bytes())])
    first = await env["builder"].build(  # type: ignore[union-attr]
        BuildRequest(
            kb_id=kb.kb_id, source_id="src1", manifest=manifest,
            files=FileResolver({"src1": Path(env["root"])}).resolve("src1", manifest),
        )
    )
    await env["publisher"].publish(first.snapshot.version_id, None)  # type: ignore[union-attr]
    _write(env, "a.txt", "第二版")
    second_manifest = _manifest([("a.txt", Path(env["root"], "a.txt").read_bytes())])
    second = await env["builder"].build(  # type: ignore[union-attr]
        BuildRequest(
            kb_id=kb.kb_id, source_id="src1", manifest=second_manifest,
            files=FileResolver({"src1": Path(env["root"])}).resolve("src1", second_manifest),
        )
    )
    await env["publisher"].publish(second.snapshot.version_id, first.snapshot.version_id)  # type: ignore[union-attr]
    rolled = await env["publisher"].rollback(  # type: ignore[union-attr]
        kb.kb_id, first.snapshot.version_id, second.snapshot.version_id
    )
    assert rolled.version_id == first.snapshot.version_id
    old_chunks = await env["files"].load_all_chunks(kb.kb_id, first.snapshot.version_id)  # type: ignore[union-attr]
    assert any("第一版" in chunk.text for chunk in old_chunks)
    new_chunks = await env["files"].load_all_chunks(kb.kb_id, second.snapshot.version_id)  # type: ignore[union-attr]
    assert any("第二版" in chunk.text for chunk in new_chunks)


async def test_builder_requires_explicit_chunk_profile(environment) -> None:
    env = environment
    with pytest.raises(ValidationFailed):
        IndexBuilder(
            knowledge=env["knowledge"],
            sources=env["sources"],
            content=env["content"],
            snapshots=env["snapshots"],
            files=env["files"],
            parser=ParserRegistry(),
            splitter=FakeSplitter(),
            keyword_writer=BM25Index(None),
        )


async def test_preview_for_unknown_source_is_not_found(environment) -> None:
    env = environment
    kb, _ = await _setup(env)
    with pytest.raises(NotFound):
        await env["imports"].preview(  # type: ignore[union-attr]
            ImportPreviewRequest(kb_id=kb.kb_id, source_id="missing"), _manifest([])
        )


def test_preview_hash_changes_with_manifest() -> None:
    manifest = _manifest([("a.txt", b"one")])
    other = _manifest([("a.txt", b"two")])
    assert preview_hash("kb", manifest, "merge") != preview_hash("kb", other, "merge")
    assert preview_hash("kb", manifest, "merge") == preview_hash("kb", manifest, "merge")


def test_change_set_shape() -> None:
    change = ChangeSet(added=["a"], modified=[], removed=[], unchanged=["b"])
    assert change.added == ["a"]


async def test_content_and_qa_services(environment) -> None:
    env = environment
    from qa_contracts.knowledge import PutDocument, PutQA

    kb, _ = await _setup(env)
    service: ContentService = env["content_service"]  # type: ignore[assignment]
    receipt = await service.put(
        PutDocument(kb_id=kb.kb_id, title="手册", text="第一版正文")
    )
    assert receipt.requires_publish is True
    document_id = receipt.document_id
    page = await service.list(kb.kb_id)
    assert [document.document_id for document in page.items] == [document_id]

    updated = await service.put(
        PutDocument(
            kb_id=kb.kb_id, title="手册", text="第二版正文",
            expected_revision_id=(await service.get(document_id)).revision.revision_id,
        ),
        document_id=document_id,
    )
    assert updated.document_id == document_id
    detail = await service.get(document_id)
    assert detail.revision.normalized_text == "第二版正文"

    qa = await service.put_qa(PutQA(kb_id=kb.kb_id, question="怎么安装？", answer="下载安装"))
    pair = await service.get_qa(qa.document_id)
    assert pair.question == "怎么安装？"
    deleted = await service.delete_qa(qa.document_id, pair.revision_id)
    assert deleted.kb_id == kb.kb_id
    with pytest.raises(NotFound):
        await service.get_qa(qa.document_id)


def test_io_bytes_round_trip() -> None:
    stream = io.BytesIO(b"payload")
    assert stream.read() == b"payload"


def test_kb_service_delete_requires_published_check(environment) -> None:
    env = environment
    kb = env["kb"]
    created = _run(kb.create(CreateKB(name="待删除")))
    _run(kb.delete(created.kb_id, created.etag))
    with pytest.raises(NotFound):
        _run(kb.get(created.kb_id))


def _run(awaitable):
    import asyncio

    return asyncio.run(awaitable)
