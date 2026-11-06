"""P2 Gate: frozen read/write port signatures independent of implementations."""

from __future__ import annotations

from typing import get_type_hints

from qa_contracts.answers import Hit
from qa_contracts.knowledge import (
    Chunk,
    ChunkProfile,
    ParsedDocument,
    SearchScope,
    SourceManifest,
    UploadBatch,
    UploadManifest,
)
from qa_contracts.operations import AccessScope
from qa_contracts.ports import ChunkSplitter, KeywordReader, SnapshotReader, UploadWriter
from qa_contracts.selection import PinnedKBTarget, ResolvedScope


def test_snapshot_resolution_returns_pinned_targets_and_authorized_search_scope() -> None:
    resolve_many = get_type_hints(SnapshotReader.resolve_many)
    assert resolve_many["return"] is ResolvedScope
    resolve = get_type_hints(SnapshotReader.resolve)
    assert resolve["access"] is AccessScope
    search_scope = get_type_hints(SnapshotReader.search_scope)
    assert search_scope["target"] is PinnedKBTarget
    assert search_scope["access"] is AccessScope
    assert search_scope["return"] is SearchScope
    chunks = get_type_hints(SnapshotReader.load_chunks)
    assert chunks["target"] is PinnedKBTarget
    assert chunks["access"] is AccessScope
    assert get_type_hints(SnapshotReader.load_revision)["access"] is AccessScope


def test_chunk_splitter_has_all_pinned_provenance_inputs() -> None:
    hints = get_type_hints(ChunkSplitter.split)
    assert hints["document"] is ParsedDocument
    assert hints["kb_id"] is str
    assert hints["version_id"] is str
    assert hints["revision_id"] is str
    assert hints["profile"] is ChunkProfile
    assert hints["return"] == list[Chunk]


def test_keyword_reader_uses_one_snapshot_scope_and_explicit_limit() -> None:
    hints = get_type_hints(KeywordReader.search)
    assert hints["scope"] is SearchScope
    assert hints["k"] is int
    assert hints["return"] == list[Hit]


def test_upload_writer_cannot_accept_client_complete_flag() -> None:
    begin = get_type_hints(UploadWriter.begin)
    finish = get_type_hints(UploadWriter.finish)
    assert begin["manifest"] is UploadManifest
    assert begin["return"] is UploadBatch
    assert finish["return"] is SourceManifest
    assert "complete" not in UploadManifest.model_fields
    assert "complete" in SourceManifest.model_fields
