"""Stage-end cross-stream check: A1 real snapshot read by A2's real keyword path.

This is the only place both backend streams are assembled. A1 publishes a real
snapshot from real files (Chunker and BM25Index are A2's algorithm ports); A2's
published-snapshot reader, router and federated retriever then consume it. No
fake snapshot, no fake hit: if either side breaks the frozen contract, this test
fails rather than the per-stream suites.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from kb_management.chunking import Chunker
from kb_management.imports import FileResolver, ImportService
from kb_management.indexing import IndexBuilder, SnapshotPublisher
from kb_management.parsers import ParserRegistry
from kb_management.service import KBService
from qa_assistant.retrieval import FederatedRetriever, HybridRetriever
from qa_assistant.routing import KnowledgeRouter
from qa_contracts.errors import PermissionDenied
from qa_contracts.knowledge import (
    ChunkProfile,
    CreateKB,
    ImportPreviewRequest,
    ImportRequest,
    ManifestFile,
    Source,
    SourceManifest,
)
from qa_contracts.models import InferenceBinding, InferencePolicy
from qa_contracts.operations import AccessScope
from qa_contracts.selection import (
    ExplicitSelection,
    KBTarget,
    ResolvedScope,
    RetrievalSelection,
    RoutingContext,
)
from qa_infrastructure.catalog import AuthorizedKnowledgeCatalog
from qa_infrastructure.indexes import BM25Index
from qa_infrastructure.repositories import (
    SQLiteContentRepository,
    SQLiteImportPreviewRepository,
    SQLiteJobRepository,
    SQLiteKnowledgeRepository,
    SQLiteSnapshotRepository,
    SQLiteSourceRepository,
)
from qa_infrastructure.snapshots import FileSnapshotStore, PublishedSnapshotReader
from qa_infrastructure.sqlite import SQLiteStore


@pytest.fixture()
async def wired(tmp_path: Path):
    database = tmp_path / "var" / "qa.sqlite3"
    creating = SQLiteStore(database)
    await creating.migrate("head")
    await creating.close()
    store = SQLiteStore(database)
    await store.open()
    knowledge = SQLiteKnowledgeRepository(store)
    sources = SQLiteSourceRepository(store)
    content = SQLiteContentRepository(store)
    snapshots = SQLiteSnapshotRepository(store)
    jobs = SQLiteJobRepository(store)
    previews = SQLiteImportPreviewRepository(store)
    files = FileSnapshotStore(tmp_path / "var" / "snapshots")
    index_root = tmp_path / "var" / "indexes"
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "install.md").write_text(
        "# 安装\n\n下载安装包并运行安装程序。\n\n# 配置\n\n修改端口后重启服务。\n",
        encoding="utf-8",
    )
    kb = await KBService(knowledge=knowledge).create(
        CreateKB(name="产品", description="安装与配置说明", routing_examples=["如何安装"])
    )
    await sources.put(
        Source(
            source_id="src1", kb_id=kb.kb_id, kind="local_root", root_id="root1",
            display_name="corpus", revision="r1",
        ),
        None,
    )
    payload = (corpus / "install.md").read_bytes()
    manifest = SourceManifest(
        source_id="src1",
        files=[
            ManifestFile(
                relative_path="install.md",
                digest=hashlib.sha256(payload).hexdigest(),
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
        files=files,
        parser=ParserRegistry(),
        splitter=Chunker(),
        keyword_writer=BM25Index(index_root),
        chunk_profile=ChunkProfile(target_tokens=120, overlap_tokens=20),
        store=store,
    )
    imports = ImportService(
        knowledge=knowledge,
        sources=sources,
        previews=previews,
        jobs=jobs,
        builder=builder,
        files=FileResolver({"src1": corpus}),
        local_roots={"root1": corpus},
        upload_root=tmp_path / "var" / "uploads",
    )
    preview = await imports.preview(
        ImportPreviewRequest(kb_id=kb.kb_id, source_id="src1"), manifest
    )
    job = await imports.apply(
        ImportRequest(
            kb_id=kb.kb_id, source_id="src1", expected_preview_hash=preview.preview_hash
        ),
        manifest,
    )
    outcome = await imports.execute(
        job, files=FileResolver({"src1": corpus}).resolve("src1", manifest)
    )
    assert outcome.failed is False, outcome.reason
    await SnapshotPublisher(
        knowledge=knowledge, snapshots=snapshots, files=files
    ).publish(outcome.snapshot.version_id, None)
    reader = PublishedSnapshotReader(
        store=store, files=files, knowledge=knowledge, snapshots=snapshots
    )
    retriever = HybridRetriever(keyword_reader=BM25Index(index_root))
    router = KnowledgeRouter(
        catalog=AuthorizedKnowledgeCatalog(source=knowledge.all),
        snapshots=reader,
        retriever=retriever,
    )
    try:
        yield {
            "kb": kb,
            "snapshot": outcome.snapshot,
            "reader": reader,
            "router": router,
            "retriever": retriever,
            "files": files,
            "store": store,
            "access": AccessScope(principal_id="p", kb_ids=[kb.kb_id]),
        }
    finally:
        await store.close()


def _binding() -> InferenceBinding:
    return InferenceBinding(binding_id="b1", policy=InferencePolicy.LOCAL_ONLY)


def _explicit(kb_id: str) -> RetrievalSelection:
    return ExplicitSelection(targets=[KBTarget(kb_id=kb_id)])


async def test_published_snapshot_is_selected_and_searched(wired) -> None:
    access = wired["access"]
    prepared = await wired["router"].prepare(
        "安装步骤", _explicit(wired["kb"].kb_id), RoutingContext(), access
    )
    result = await wired["router"].select(
        "安装步骤", prepared, RoutingContext(), _binding()
    )
    assert result.status.value == "resolved"
    assert result.targets[0].version_id == wired["snapshot"].version_id

    scope = ResolvedScope(scope_id=result.reason or "scope", targets=result.targets)
    hits = await FederatedRetriever(
        retriever=wired["retriever"], snapshots=wired["reader"]
    ).retrieve("安装步骤", scope, _binding(), 5, access=access)
    assert hits, "A2 keyword retrieval must read the A1-sealed snapshot"
    assert all(
        (hit.kb_id, hit.version_id) == (wired["kb"].kb_id, wired["snapshot"].version_id)
        for hit in hits
    )
    assert any("安装" in hit.text for hit in hits)


async def test_search_scope_comes_from_the_published_snapshot(wired) -> None:
    pinned = wired["snapshot"]
    scope = await wired["reader"].search_scope(
        _pinned(wired["kb"].kb_id, pinned.version_id), wired["access"]
    )
    assert scope.version_id == pinned.version_id
    assert scope.keyword_profile == pinned.keyword_profile
    assert scope.index_ref == pinned.keyword_index_ref
    chunks = await wired["files"].load_all_chunks(wired["kb"].kb_id, pinned.version_id)
    assert {chunk.revision_id for chunk in chunks} == set(
        pinned.document_revisions.values()
    )


async def test_unauthorized_reader_is_denied_before_any_read(wired) -> None:
    with pytest.raises(PermissionDenied):
        await wired["reader"].resolve(
            wired["kb"].kb_id,
            wired["snapshot"].version_id,
            AccessScope(principal_id="other", kb_ids=[]),
        )


def _pinned(kb_id: str, version_id: str):
    from qa_contracts.selection import PinnedKBTarget

    return PinnedKBTarget(kb_id=kb_id, version_id=version_id)
