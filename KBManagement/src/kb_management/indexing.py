"""Incremental snapshot building and publishing (A1 owns the transaction).

The algorithm ports are supplied by A2 (``ChunkSplitter``, ``KeywordIndexWriter``)
and consumed without importing ``qa_assistant``. Order of operations:

1. compute the change set from a server-verified manifest against the baseline;
2. reuse unchanged revisions (no re-parse, no re-chunk, no re-index);
3. parse only changed files, recording a per-file diagnostic for every failure;
4. write every chunk and revision file into a staging directory and seal it;
5. record the READY snapshot row;
6. only an explicit publish moves the database pointer, with compare-and-swap.

A failure at any step before publish leaves the active version untouched.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from qa_contracts.base import ID, utc_now
from qa_contracts.errors import Conflict, ErrorDetail, ValidationFailed
from qa_contracts.knowledge import (
    ChangeSet,
    Chunk,
    ChunkProfile,
    ContentKind,
    Locator,
    ParsedBlock,
    ParsedDocument,
    QAPair,
    Revision,
    Snapshot,
    SnapshotState,
    SourceManifest,
)
from qa_contracts.operations import JobFileDiagnostic


class ChunkSplitterPort(Protocol):
    def split(
        self,
        document: ParsedDocument,
        *,
        kb_id: str,
        version_id: str,
        revision_id: str,
        profile: ChunkProfile,
    ) -> list[Chunk]: ...


class KeywordIndexWriterPort(Protocol):
    async def build(self, chunks: list[Chunk], profile: str) -> str: ...


class ParserPort(Protocol):
    async def parse(
        self, kind: str, stream: object, options: object = ...
    ) -> ParsedDocument: ...


@dataclass(slots=True)
class BuildRequest:
    kb_id: str
    #: ``None`` means a whole-base rebuild (documents + QA pairs, no file source).
    source_id: str | None = None
    manifest: SourceManifest | None = None
    #: Server-authorized local paths for the files in this manifest.
    files: Mapping[str, Path] = field(default_factory=dict)
    mode: str = "merge"
    #: Cooperative cancellation; checked between files and before committing.
    should_cancel: Callable[[], Awaitable[bool]] | None = None


@dataclass(slots=True)
class BuildOutcome:
    snapshot: Snapshot | None
    diagnostics: list[JobFileDiagnostic] = field(default_factory=list)
    parsed_paths: list[str] = field(default_factory=list)
    reused_paths: list[str] = field(default_factory=list)
    failed: bool = False
    cancelled: bool = False
    reason: str = ""


@dataclass(slots=True)
class ValidationReport:
    ok: bool = False
    problems: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ReusePlan:
    reused_paths: list[str] = field(default_factory=list)
    reparsed_paths: list[str] = field(default_factory=list)


class ChangePlanner:
    """Pure diff; a partial or failed scan can never produce removals."""

    @staticmethod
    def diff(
        previous: SourceManifest | None,
        current: SourceManifest,
        mode: str = "merge",
    ) -> ChangeSet:
        previous_entries = (
            {entry.relative_path: entry.digest for entry in previous.files}
            if previous is not None
            else {}
        )
        current_entries = {entry.relative_path: entry.digest for entry in current.files}
        added: list[str] = []
        modified: list[str] = []
        unchanged: list[str] = []
        for path in sorted(current_entries):
            if path not in previous_entries:
                added.append(path)
            elif previous_entries[path] != current_entries[path]:
                modified.append(path)
            else:
                unchanged.append(path)
        removed: list[str] = []
        if mode == "mirror" and current.complete and current.scan_status == "succeeded":
            removed = sorted(set(previous_entries) - set(current_entries))
        return ChangeSet(added=added, modified=modified, removed=removed, unchanged=unchanged)


class IndexBuilder:
    """Builds a complete, verifiable snapshot from a verified source manifest."""

    def __init__(
        self,
        *,
        knowledge: object,
        sources: object,
        content: object,
        snapshots: object,
        files: object,
        parser: ParserPort,
        splitter: ChunkSplitterPort,
        keyword_writer: KeywordIndexWriterPort,
        chunk_profile: ChunkProfile | None = None,
        keyword_profile: str = "zh-bm25-v1",
        store: object | None = None,
        qa_pairs: object | None = None,
    ) -> None:
        if chunk_profile is None:
            raise ValidationFailed(
                [
                    ErrorDetail(
                        field="chunk_profile",
                        reason=(
                            "must be chosen explicitly after corpus analysis;"
                            " no implicit default"
                        ),
                    )
                ]
            )
        self._knowledge = knowledge
        self._sources = sources
        self._content = content
        self._snapshots = snapshots
        self._files = files
        self._parser = parser
        self._splitter = splitter
        self._keyword_writer = keyword_writer
        self._store = store
        self._qa_pairs = qa_pairs
        self.chunk_profile = chunk_profile
        self.keyword_profile = keyword_profile

    async def build(self, request: BuildRequest) -> BuildOutcome:
        """Rebuild a snapshot from every repository in the base, not just files.

        A source import supplies ``source_id`` + ``manifest``; a manual rebuild
        passes neither and indexes the whole base (documents plus QA pairs).
        """
        await self._knowledge.get(request.kb_id)
        base = await self._base_snapshot(request.kb_id)
        previous = None
        if request.source_id is not None and await self._sources.has_baseline(
            request.source_id
        ):
            previous = await self._sources.get_manifest(request.source_id, base or "")
        change = (
            ChangePlanner.diff(previous, request.manifest, request.mode)
            if request.manifest is not None
            else None
        )
        outcome = BuildOutcome(snapshot=None)
        from_source = change is not None

        if await self._cancelled(request):
            outcome.cancelled = True
            outcome.reason = "cancelled before building a snapshot"
            return outcome

        if from_source and base and not (
            change.added or change.modified or change.removed
        ):
            base_snapshot = await self._snapshots.get(base)
            await self._files.verify(base_snapshot.kb_id, base_snapshot.version_id)
            await self._sources.save_manifest(
                request.source_id,
                base,
                _baseline_for(request.manifest, base_snapshot.indexed_file_ids),
            )
            outcome.reused_paths = list(change.unchanged)
            outcome.snapshot = base_snapshot
            return outcome

        version_id = f"ver_{uuid.uuid4().hex}"
        handle = await self._files.stage(
            sorted(change.added + change.modified + change.unchanged)
            if from_source else [],
            kb_id=request.kb_id,
            version_id=version_id,
        )
        chunks: list[Chunk] = []
        document_revisions: dict[str, str] = {}
        indexed_files: list[str] = []
        pending_revisions: list[Revision] = []
        expected_revisions: dict[str, str | None] = {}
        try:
            base_chunks = await self._chunks_by_revision(base)
            if from_source:
                await self._index_source_base(
                    request, handle, version_id, base_chunks, chunks,
                    document_revisions, outcome, change,
                )
            else:
                await self._index_repository(
                    request, handle, version_id, base_chunks, chunks,
                    document_revisions, outcome,
                )
            for path in sorted(change.added + change.modified) if from_source else []:
                if await self._cancelled(request):
                    await self._files.discard(handle)
                    outcome.cancelled = True
                    outcome.reason = "cancelled before building a snapshot"
                    return outcome
                parsed, revision = await self._parse_and_record(
                    request, path, outcome
                )
                if parsed is None or revision is None:
                    continue
                new_chunks = self._splitter.split(
                    parsed,
                    kb_id=request.kb_id,
                    version_id=version_id,
                    revision_id=revision.revision_id,
                    profile=self.chunk_profile,
                )
                chunks.extend(new_chunks)
                document_revisions[revision.document_id] = revision.revision_id
                indexed_files.append(path)
                pending_revisions.append(revision)
                expected_revisions[revision.document_id] = (
                    None if revision.parent_revision_id is None else revision.parent_revision_id
                )
                outcome.parsed_paths.append(path)
                await self._files.write_revision(handle, revision)

            for path in change.unchanged if from_source else []:
                if await self._cancelled(request):
                    await self._files.discard(handle)
                    outcome.cancelled = True
                    outcome.reason = "cancelled before building a snapshot"
                    return outcome
                document = await self._content.find_by_path(request.source_id, path)
                if document is None:
                    outcome.diagnostics.append(
                        JobFileDiagnostic(
                            relative_path=path,
                            status="failed",
                            message="unchanged file has no stored document",
                        )
                    )
                    continue
                revision = await self._content.latest_revision(document.document_id)
                document_revisions[document.document_id] = revision.revision_id
                indexed_files.append(path)
                outcome.reused_paths.append(path)
                await self._files.write_revision(handle, revision)
                reused = _rebased_chunks(
                    base_chunks.get(revision.revision_id), version_id
                )
                if reused is None:
                    parsed = await self._reparse(request, path, outcome)
                    if parsed is None:
                        continue
                    reused = self._splitter.split(
                        parsed,
                        kb_id=request.kb_id,
                        version_id=version_id,
                        revision_id=revision.revision_id,
                        profile=self.chunk_profile,
                    )
                    outcome.parsed_paths.append(path)
                chunks.extend(reused)

            for path in change.removed if from_source else []:
                document = await self._content.find_by_path(request.source_id, path)
                if document is not None:
                    document_revisions.pop(document.document_id, None)

            if not chunks:
                await self._files.discard(handle)
                outcome.failed = True
                outcome.reason = "no indexable content in the selected scope"
                return outcome

            await self._files.append_chunks(handle, chunks)
            if await self._cancelled(request):
                # Last safe point: nothing has been sealed or committed yet.
                await self._files.discard(handle)
                outcome.cancelled = True
                outcome.reason = "cancelled before sealing the snapshot"
                return outcome
            index_ref = await self._keyword_writer.build(chunks, self.keyword_profile)
            if await self._cancelled(request):
                # The keyword build can be slow; a cancel that arrived while it
                # ran must still leave the database and the source baseline
                # untouched, otherwise the next import would reuse a revision
                # that no active snapshot contains and lose the change.
                await self._files.discard(handle)
                outcome.cancelled = True
                outcome.reason = "cancelled while building the keyword index"
                return outcome
            snapshot = Snapshot(
                version_id=version_id,
                kb_id=request.kb_id,
                parent_version_id=base,
                state=SnapshotState.READY,
                # ``indexed_file_ids`` lists source-relative paths only; a
                # whole-base rebuild records its content in ``document_revisions``.
                indexed_file_ids=sorted(indexed_files),
                document_revisions=document_revisions,
                keyword_profile=self.keyword_profile,
                keyword_index_ref=index_ref,
                vector_index="absent",
                created_at=utc_now(),
            )
            report = self.validate(snapshot)
            if not report.ok:
                await self._files.discard(handle)
                outcome.failed = True
                outcome.reason = "; ".join(report.problems)
                return outcome
            if await self._cancelled(request):
                await self._files.discard(handle)
                outcome.cancelled = True
                outcome.reason = "cancelled before sealing the snapshot"
                return outcome
            await self._files.seal(handle, kb_id=request.kb_id, version_id=version_id)
            # Destructive bookkeeping happens only after the files are sealed:
            # a failure above leaves documents and the baseline untouched.
            committed = await self._commit(
                snapshot,
                request,
                change.removed if change is not None else [],
                indexed_files,
                pending_revisions,
                expected_revisions,
            )
            if not committed:
                # Cancelled inside the transaction: nothing was written. The
                # sealed directory is unreferenced; a later cleanup may remove it.
                outcome.cancelled = True
                outcome.reason = "cancelled before committing the snapshot"
                return outcome
            outcome.snapshot = snapshot
            return outcome
        except BaseException:
            await self._files.discard(handle)
            raise

    async def _commit(
        self,
        snapshot: Snapshot,
        request: BuildRequest,
        removed: list[str],
        indexed_files: list[str],
        pending_revisions: list[Revision],
        expected_revisions: dict[str, str | None],
    ) -> bool:
        """Write snapshot + baseline atomically; return False if cancelled first."""
        async with self._transaction():
            if await self._cancelled(request):
                return False
            for revision in pending_revisions:
                document = await self._content.find_by_path(
                    revision.source_id, revision.relative_path
                )
                await self._content.append_revision(
                    revision.document_id,
                    revision,
                    None if document is None else document.latest_revision_id,
                    kb_id=request.kb_id,
                    title=(revision.relative_path or revision.document_id).rsplit("/", 1)[-1],
                )
            for path in removed:
                document = await self._content.find_by_path(request.source_id, path)
                if document is not None:
                    await self._content.mark_deleted(document.document_id, None)
            await self._snapshots.save(snapshot)
            if request.source_id is not None and request.manifest is not None:
                await self._sources.save_manifest(
                    request.source_id,
                    snapshot.version_id,
                    _baseline_for(request.manifest, indexed_files),
                )
        return True

    async def _index_source_base(
        self,
        request: BuildRequest,
        handle: ID,
        version_id: ID,
        base_chunks: dict[str, list[Chunk]],
        chunks: list[Chunk],
        document_revisions: dict[str, str],
        outcome: BuildOutcome,
        change: ChangeSet,
    ) -> None:
        """Carry forward KB content outside the source delta being rebuilt."""
        replaced_paths = set(change.added + change.modified + change.removed + change.unchanged)
        for document in await self._content.list_active_documents(request.kb_id):
            if await self._cancelled(request):
                return
            if document.content_kind != ContentKind.DOCUMENT:
                continue
            revision = await self._content.latest_revision(document.document_id)
            if revision.source_id == request.source_id and revision.relative_path in replaced_paths:
                continue
            document_revisions[document.document_id] = revision.revision_id
            await self._files.write_revision(handle, revision)
            reused = _rebased_chunks(base_chunks.get(revision.revision_id), version_id)
            if reused is None:
                reused = self._splitter.split(
                    _stored_document(revision),
                    kb_id=request.kb_id,
                    version_id=version_id,
                    revision_id=revision.revision_id,
                    profile=self.chunk_profile,
                )
                outcome.parsed_paths.append(document.document_id)
            chunks.extend(reused)
        if self._qa_pairs is None:
            return
        for pair in await self._qa_pairs.list_active(request.kb_id):
            if await self._cancelled(request):
                return
            revision = await self._content.latest_revision(pair.qa_id)
            document_revisions[pair.qa_id] = revision.revision_id
            await self._files.write_revision(handle, revision)
            reused = _rebased_chunks(base_chunks.get(revision.revision_id), version_id)
            if reused is None:
                reused = self._splitter.split(
                    _qa_document(pair),
                    kb_id=request.kb_id,
                    version_id=version_id,
                    revision_id=revision.revision_id,
                    profile=self.chunk_profile,
                )
                outcome.parsed_paths.append(pair.qa_id)
            chunks.extend(reused)

    async def _index_repository(
        self,
        request: BuildRequest,
        handle: ID,
        version_id: ID,
        base_chunks: dict[str, list[Chunk]],
        chunks: list[Chunk],
        document_revisions: dict[str, str],
        outcome: BuildOutcome,
        *,
        excluded_source_paths: set[str] | None = None,
        excluded_source_id: str | None = None,
    ) -> None:
        """Index live KB records, optionally excluding source paths being changed."""
        excluded_source_paths = excluded_source_paths or set()
        documents = [
            document
            for document in await self._content.list_active_documents(request.kb_id)
            if document.content_kind == ContentKind.DOCUMENT
        ]
        for document in documents:
            if await self._cancelled(request):
                return
            revision = await self._content.latest_revision(document.document_id)
            if (
                excluded_source_id is not None
                and revision.source_id == excluded_source_id
                and revision.relative_path in excluded_source_paths
            ):
                continue
            document_revisions[document.document_id] = revision.revision_id
            await self._files.write_revision(handle, revision)
            reused = _rebased_chunks(base_chunks.get(revision.revision_id), version_id)
            if reused is None:
                parsed = _stored_document(revision)
                reused = self._splitter.split(
                    parsed,
                    kb_id=request.kb_id,
                    version_id=version_id,
                    revision_id=revision.revision_id,
                    profile=self.chunk_profile,
                )
                outcome.parsed_paths.append(document.document_id)
            chunks.extend(reused)
        if self._qa_pairs is None:
            return
        for pair in await self._qa_pairs.list_active(request.kb_id):
            if await self._cancelled(request):
                return
            revision = await self._content.latest_revision(pair.qa_id)
            document_revisions[pair.qa_id] = revision.revision_id
            await self._files.write_revision(handle, revision)
            reused = _rebased_chunks(base_chunks.get(revision.revision_id), version_id)
            if reused is None:
                parsed = _qa_document(pair)
                reused = self._splitter.split(
                    parsed,
                    kb_id=request.kb_id,
                    version_id=version_id,
                    revision_id=revision.revision_id,
                    profile=self.chunk_profile,
                )
                outcome.parsed_paths.append(pair.qa_id)
            chunks.extend(reused)

    def _transaction(self):  # type: ignore[no-untyped-def]
        if self._store is None:
            from contextlib import asynccontextmanager

            @asynccontextmanager
            async def _noop():
                yield None

            return _noop()
        return self._store.transaction()

    async def _cancelled(self, request: BuildRequest) -> bool:
        return request.should_cancel is not None and await request.should_cancel()

    async def _parse_and_record(
        self, request: BuildRequest, path: str, outcome: BuildOutcome
    ) -> tuple[ParsedDocument | None, Revision | None]:
        parsed = await self._reparse(request, path, outcome)
        if parsed is None:
            return None, None
        document = await self._content.find_by_path(request.source_id, path)
        revision = Revision(
            revision_id=f"rev_{uuid.uuid4().hex}",
            document_id=document.document_id if document else f"doc_{uuid.uuid4().hex}",
            parent_revision_id=document.latest_revision_id if document else None,
            content_kind=ContentKind.DOCUMENT,
            source_id=request.source_id,
            relative_path=path,
            normalized_text="\n\n".join(block.text for block in parsed.blocks),
            diagnostics=list(parsed.diagnostics),
        )
        return parsed, revision

    async def _reparse(
        self, request: BuildRequest, path: str, outcome: BuildOutcome
    ) -> ParsedDocument | None:
        from .parsers import ParseFailure, ParseOptions, detect_kind

        kind = detect_kind(path)
        if kind is None:
            outcome.diagnostics.append(
                JobFileDiagnostic(
                    relative_path=path, status="skipped", message="unsupported file type"
                )
            )
            return None
        local = request.files.get(path)
        if local is None or not Path(local).is_file():
            outcome.diagnostics.append(
                JobFileDiagnostic(
                    relative_path=path, status="failed", message="file bytes are unavailable"
                )
            )
            return None
        try:
            with Path(local).open("rb") as stream:
                return await self._parser.parse(kind, stream, ParseOptions())
        except ParseFailure as failure:
            outcome.diagnostics.append(
                JobFileDiagnostic(
                    relative_path=path,
                    status="failed",
                    message=f"{failure.code}: {failure.message}",
                )
            )
            return None

    async def _base_snapshot(self, kb_id: str) -> str | None:
        kb = await self._knowledge.get(kb_id)
        return kb.active_version_id

    async def _chunks_by_revision(
        self, version_id: str | None
    ) -> dict[str, list[Chunk]]:
        if not version_id:
            return {}
        snapshot = await self._snapshots.get(version_id)
        try:
            chunks = await self._files.load_all_chunks(
                snapshot.kb_id, snapshot.version_id
            )
        except Exception:
            return {}
        grouped: dict[str, list[Chunk]] = {}
        for chunk in chunks:
            grouped.setdefault(chunk.revision_id, []).append(chunk)
        return grouped

    def reuse_unchanged(self, change: ChangeSet, base: str | None) -> ReusePlan:
        del base
        return ReusePlan(
            reused_paths=list(change.unchanged),
            reparsed_paths=list(change.added + change.modified),
        )

    def validate(self, staged: Snapshot) -> ValidationReport:
        report = ValidationReport()
        if not staged.keyword_profile or not staged.keyword_index_ref:
            report.problems.append("ready snapshot requires a keyword index and profile")
        if not staged.document_revisions:
            report.problems.append("snapshot has no document revision mapping")
        if len(set(staged.document_revisions.values())) != len(
            staged.document_revisions
        ):
            report.problems.append("one revision is mapped to several documents")
        if not staged.document_revisions:
            report.problems.append("snapshot has no indexed documents or QA pairs")
        report.ok = not report.problems
        return report


class SnapshotPublisher:
    """Compare-and-swap active pointer; failures leave the old version serving."""

    def __init__(self, *, knowledge: object, snapshots: object, files: object) -> None:
        self._knowledge = knowledge
        self._snapshots = snapshots
        self._files = files

    async def publish(self, version_id: str, expected_active: str | None) -> Snapshot:
        snapshot = await self._snapshots.get(version_id)
        if snapshot.state not in {
            SnapshotState.READY,
            SnapshotState.PUBLISHED,
        }:
            raise Conflict("ready version", f"state {snapshot.state.value}")
        if not await self._files.verify(snapshot.kb_id, snapshot.version_id):
            raise Conflict("verified snapshot files", "incomplete or corrupt snapshot")
        swapped = await self._snapshots.compare_and_swap_active(
            snapshot.kb_id, expected_active, version_id
        )
        if not swapped:
            current = await self._knowledge.get(snapshot.kb_id)
            raise Conflict(
                f"active version {expected_active}",
                f"active version {current.active_version_id}",
            )
        published = snapshot.model_copy(update={"state": SnapshotState.PUBLISHED})
        await self._snapshots.save(published)
        return published

    async def rollback(
        self, kb_id: str, target: str, expected_active: str | None
    ) -> Snapshot:
        snapshot = await self._snapshots.get(target)
        if snapshot.kb_id != kb_id:
            raise Conflict(f"version of {kb_id}", f"version of {snapshot.kb_id}")
        if snapshot.state not in {SnapshotState.READY, SnapshotState.PUBLISHED}:
            raise Conflict("ready version", f"state {snapshot.state.value}")
        if not await self._files.verify(snapshot.kb_id, snapshot.version_id):
            raise Conflict("verified snapshot files", "incomplete or corrupt snapshot")
        swapped = await self._snapshots.compare_and_swap_active(
            kb_id, expected_active, target
        )
        if not swapped:
            current = await self._knowledge.get(kb_id)
            raise Conflict(
                f"active version {expected_active}",
                f"active version {current.active_version_id}",
            )
        if snapshot.state == SnapshotState.PUBLISHED:
            return snapshot
        published = snapshot.model_copy(update={"state": SnapshotState.PUBLISHED})
        await self._snapshots.save(published)
        return published


def _stored_document(revision: Revision) -> ParsedDocument:
    """Chunk the stored normalized text; there is no source file to re-parse."""
    return ParsedDocument(
        blocks=[
            ParsedBlock(
                text=revision.normalized_text,
                locator=Locator(kind="text_lines", start_line=1, end_line=1),
                heading=revision.relative_path or revision.document_id,
            )
        ]
        if revision.normalized_text.strip()
        else [],
        diagnostics=list(revision.diagnostics),
    )


def _qa_document(pair: QAPair) -> ParsedDocument:
    """A QA pair is chunked as one record with a field-level locator."""
    text = "\n".join(["Question: " + pair.question, "Answer: " + pair.answer])
    return ParsedDocument(
        blocks=[
            ParsedBlock(
                text=text,
                locator=Locator(kind="qa_fields"),
                heading=pair.question[:200],
            )
        ]
    )


def _rebased_chunks(chunks: list[Chunk] | None, version_id: str) -> list[Chunk] | None:
    """Reuse unchanged text and locators under the new snapshot identity."""
    if not chunks:
        return None
    return [chunk.model_copy(update={"version_id": version_id}) for chunk in chunks]


def _baseline_for(manifest: SourceManifest, indexed_files: list[str]) -> SourceManifest:
    """Only files actually indexed become the baseline.

    If a file failed to parse, it stays out of the baseline so the next import
    treats it as new instead of silently reusing a missing revision.
    """
    indexed = set(indexed_files)
    return manifest.model_copy(
        update={"files": [entry for entry in manifest.files
                          if entry.relative_path in indexed]}
    )


__all__ = [
    "BuildOutcome",
    "BuildRequest",
    "ChangePlanner",
    "IndexBuilder",
    "ReusePlan",
    "SnapshotPublisher",
    "ValidationReport",
]
