"""Standalone P2 A2 index/chunk/catalog checks; no A1 store or live service."""

from __future__ import annotations

import pytest

from kb_management.chunking import Chunker
from qa_contracts.errors import NotFound, PermissionDenied
from qa_contracts.knowledge import (
    ChunkProfile,
    KnowledgeBase,
    Locator,
    LocatorKind,
    ParsedBlock,
    ParsedDocument,
    SearchScope,
)
from qa_contracts.operations import AccessScope
from qa_contracts.selection import CatalogQuery
from qa_infrastructure.catalog import AuthorizedKnowledgeCatalog
from qa_infrastructure.indexes import BM25Index, ChineseTokenizer


def _document(text: str) -> ParsedDocument:
    return ParsedDocument(
        blocks=[
            ParsedBlock(
                text=text,
                locator=Locator(kind=LocatorKind.TEXT_LINES, start_line=1, end_line=1),
            )
        ]
    )


def test_structure_aware_chunks_are_pinned_stable_and_locatable() -> None:
    source = _document("部署指南 ERR-404：请检查配置。步骤二：重新启动服务。")
    chunker = Chunker()
    profile = ChunkProfile(target_tokens=9, overlap_tokens=2)
    chunks = chunker.split(source, kb_id="kb", version_id="v1", revision_id="r1", profile=profile)
    again = chunker.split(source, kb_id="kb", version_id="v1", revision_id="r1", profile=profile)
    assert len(chunks) > 1
    assert [chunk.chunk_id for chunk in again] == [chunk.chunk_id for chunk in chunks]
    assert [chunk.ordinal for chunk in chunks] == list(range(len(chunks)))
    assert all(
        (chunk.kb_id, chunk.version_id, chunk.revision_id) == ("kb", "v1", "r1") for chunk in chunks
    )
    assert all(chunker.map_locator(chunk, source.blocks) == chunk.locator for chunk in chunks)
    assert (
        chunks[0].chunk_id
        != chunker.split(source, kb_id="kb", version_id="v2", revision_id="r1", profile=profile)[
            0
        ].chunk_id
    )
    assert "ERR-404" in " ".join(chunk.text for chunk in chunks)


def test_table_chunks_repeat_real_header_without_invented_coordinates() -> None:
    block = ParsedBlock(
        text="代码|说明\nERR-404|资源不存在\nERR-409|版本冲突",
        locator=Locator(kind=LocatorKind.WORD_TABLE, paragraph=3),
    )
    chunks = Chunker().split(
        ParsedDocument(blocks=[block]),
        kb_id="kb",
        version_id="v1",
        revision_id="r1",
        profile=ChunkProfile(target_tokens=8, overlap_tokens=1),
    )
    assert len(chunks) == 2
    assert all(chunk.text.startswith("代码|说明\n") for chunk in chunks)
    assert all(chunk.locator == block.locator for chunk in chunks)

    excel = block.model_copy(
        update={
            "locator": Locator(kind=LocatorKind.EXCEL_RANGE, sheet="Sheet1", cell_range="A1:B3")
        }
    )
    excel_chunks = Chunker().split(
        ParsedDocument(blocks=[excel]),
        kb_id="kb",
        version_id="v1",
        revision_id="r1",
        profile=ChunkProfile(target_tokens=8, overlap_tokens=1),
    )
    assert all(chunk.text.startswith("代码|说明\n") for chunk in excel_chunks)
    assert all(chunk.locator == excel.locator for chunk in excel_chunks)
    assert all(Chunker().map_locator(chunk, [excel]) == excel.locator for chunk in excel_chunks)


@pytest.mark.asyncio
async def test_chinese_and_identifier_bm25_reads_pinned_snapshot(tmp_path) -> None:
    index = BM25Index(tmp_path)
    chunks = Chunker().split(
        ParsedDocument(
            blocks=[
                *_document("配置 ERR-404 的处理流程").blocks,
                *_document("人事休假申请步骤").blocks,
            ]
        ),
        kb_id="kb-a",
        version_id="v1",
        revision_id="r1",
        profile=ChunkProfile(target_tokens=40, overlap_tokens=3),
    )
    ref = await index.build(chunks, profile="zh-v1")
    scope = SearchScope(kb_id="kb-a", version_id="v1", keyword_profile="zh-v1", index_ref=ref)
    assert "err-404" in ChineseTokenizer().tokenize("配置 ERR-404")
    assert "配" in ChineseTokenizer().tokenize("配置")
    assert (await BM25Index(tmp_path).search("ERR-404", scope, 1))[0].chunk_id == chunks[0].chunk_id
    assert (await index.search("休假", scope, 1))[0].chunk_id == chunks[1].chunk_id
    assert len(await index.search("配置 ERR-404", scope, 1)) == 1
    assert await index.search("不存在的罕见词", scope, 5) == []
    with pytest.raises(ValueError, match="pinned search scope"):
        await index.search("配置", scope.model_copy(update={"version_id": "v2"}), 3)
    with pytest.raises(ValueError, match="pinned search scope"):
        await index.search("配置", scope.model_copy(update={"keyword_profile": "other"}), 3)
    with pytest.raises(NotFound):
        await index.search("配置", scope.model_copy(update={"index_ref": "0" * 64}), 3)
    with pytest.raises(ValueError, match="empty keyword index"):
        await index.build([], "zh-v1")
    with pytest.raises(ValueError, match="one KB and version"):
        await index.build([chunks[0], chunks[1].model_copy(update={"kb_id": "kb-b"})], "zh-v1")


@pytest.mark.asyncio
async def test_catalog_filters_published_and_authorized_and_reads_live_metadata() -> None:
    items = [
        KnowledgeBase(kb_id="kb-a", name="产品", active_version_id="v1", etag="e"),
        KnowledgeBase(kb_id="kb-b", name="运维", active_version_id="v2", etag="e"),
        KnowledgeBase(kb_id="kb-c", name="私有", active_version_id="v1", etag="e"),
        KnowledgeBase(kb_id="kb-d", name="草稿", etag="e"),
    ]

    async def load():
        return items

    catalog = AuthorizedKnowledgeCatalog(load)
    access = AccessScope(principal_id="p", kb_ids=["kb-a", "kb-b", "kb-d"])
    first = await catalog.list_authorized(access, CatalogQuery(limit=1))
    assert [item.kb_id for item in first.items] == ["kb-a"]
    assert first.next_cursor == "kb-a"
    assert [
        item.kb_id
        for item in (
            await catalog.list_authorized(access, CatalogQuery(limit=1, cursor=first.next_cursor))
        ).items
    ] == ["kb-b"]
    for forbidden in ("kb-c", "kb-d", "missing"):
        with pytest.raises(PermissionDenied):
            await catalog.get_authorized(access, ["kb-a", forbidden])
    items[0] = items[0].model_copy(update={"active_version_id": "v3"})
    assert (await catalog.get_authorized(access, ["kb-a"]))[0].version_id == "v3"
