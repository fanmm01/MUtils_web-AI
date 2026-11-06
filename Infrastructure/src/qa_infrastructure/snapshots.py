"""Immutable snapshot files and the authorized published-snapshot reader.

A snapshot directory is built under ``staging/`` and renamed into
``<kb_id>/<version_id>/`` only after every file is written and verified. Old
versions are never overwritten: a rollback simply points at an existing
directory. Publishing to the active pointer is the database's job; this module
only guarantees that the files behind a ready version are complete.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
from pathlib import Path

from qa_contracts.base import ID
from qa_contracts.errors import Conflict, NotFound, ResourceGone
from qa_contracts.knowledge import Chunk, Revision, SearchScope, Snapshot, SnapshotState
from qa_contracts.operations import AccessScope
from qa_contracts.selection import KBTarget, PinnedKBTarget, ResolvedScope

from .repositories import SQLiteKnowledgeRepository, SQLiteSnapshotRepository
from .sqlite import SQLiteStore

CHUNKS_FILE = "chunks.jsonl"
MANIFEST_FILE = "snapshot.json"
REVISION_DIR = "revisions"


class FileSnapshotStore:
    """Stages a complete directory, then seals it with a manifest digest."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    # -- staging ----------------------------------------------------------
    async def stage(
        self, manifest: list[str], *, kb_id: ID, version_id: ID
    ) -> ID:
        return await asyncio.to_thread(self._stage_sync, manifest, kb_id, version_id)

    def _stage_sync(self, manifest: list[str], kb_id: ID, version_id: ID) -> ID:
        handle = f"{_safe(kb_id)}--{_safe(version_id)}"
        staging = self.root / "staging" / handle
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        (staging / CHUNKS_FILE).write_text("", encoding="utf-8")
        (staging / MANIFEST_FILE).write_text(
            json.dumps({"files": sorted(manifest)}, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        return handle

    async def append_chunks(self, handle: ID, chunks: list[Chunk]) -> None:
        await asyncio.to_thread(self._append_chunks_sync, handle, chunks)

    def _append_chunks_sync(self, handle: ID, chunks: list[Chunk]) -> None:
        staging = self._staging(handle)
        with (staging / CHUNKS_FILE).open("a", encoding="utf-8") as stream:
            for chunk in chunks:
                stream.write(chunk.model_dump_json() + "\n")

    async def write_revision(self, handle: ID, revision: Revision) -> None:
        await asyncio.to_thread(self._write_revision_sync, handle, revision)

    def _write_revision_sync(self, handle: ID, revision: Revision) -> None:
        target = self._staging(handle) / REVISION_DIR
        target.mkdir(parents=True, exist_ok=True)
        (target / f"{revision.revision_id}.json").write_text(
            revision.model_dump_json(), encoding="utf-8"
        )

    async def seal(self, handle: ID, *, kb_id: ID, version_id: ID) -> ID:
        return await asyncio.to_thread(self._seal_sync, handle, kb_id, version_id)

    def _seal_sync(self, handle: ID, kb_id: ID, version_id: ID) -> ID:
        staging = self._staging(handle)
        digests = {
            path.relative_to(staging).as_posix(): _digest(path)
            for path in sorted(staging.rglob("*"))
            if path.is_file() and path.name != MANIFEST_FILE
        }
        sealed = dict(json.loads((staging / MANIFEST_FILE).read_text(encoding="utf-8")))
        sealed["kb_id"] = kb_id
        sealed["version_id"] = version_id
        sealed["digests"] = digests
        (staging / MANIFEST_FILE).write_text(
            json.dumps(sealed, ensure_ascii=False, sort_keys=True), encoding="utf-8"
        )
        final = self.version_dir(kb_id, version_id)
        if final.exists():
            raise Conflict(f"new version {version_id}", f"existing {version_id}")
        final.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staging, final)
        return version_id

    async def discard(self, handle: ID) -> None:
        await asyncio.to_thread(self._discard_sync, handle)

    def _discard_sync(self, handle: ID) -> None:
        staging = self.root / "staging" / handle
        if staging.exists():
            shutil.rmtree(staging)

    # -- reading ----------------------------------------------------------
    def version_dir(self, kb_id: ID, version_id: ID) -> Path:
        return self.root / "versions" / _safe(kb_id) / _safe(version_id)

    async def open(self, kb_id: ID, version_id: ID) -> Path:
        path = self.version_dir(kb_id, version_id)
        if not path.is_dir():
            raise NotFound("version files")
        return path

    async def verify(self, kb_id: ID, version_id: ID) -> bool:
        path = self.version_dir(kb_id, version_id)
        if not path.is_dir():
            return False
        return await asyncio.to_thread(_verify_dir, path, kb_id, version_id)

    async def load_chunks(self, kb_id: ID, version_id: ID, ids: list[ID]) -> list[Chunk]:
        return await asyncio.to_thread(self._load_chunks_sync, kb_id, version_id, set(ids))

    def _load_chunks_sync(self, kb_id: ID, version_id: ID, wanted: set[str]) -> list[Chunk]:
        directory = self.version_dir(kb_id, version_id)
        if not _verify_dir(directory, kb_id, version_id):
            raise ResourceGone("snapshot files")
        path = directory / CHUNKS_FILE
        if not path.is_file():
            raise NotFound("chunk file")
        found: list[Chunk] = []
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                chunk = Chunk.model_validate_json(line)
                if chunk.chunk_id in wanted and (chunk.kb_id, chunk.version_id) == (
                    kb_id,
                    version_id,
                ):
                    found.append(chunk)
        return found

    async def load_all_chunks(self, kb_id: ID, version_id: ID) -> list[Chunk]:
        return await asyncio.to_thread(self._load_all_sync, kb_id, version_id)

    def _load_all_sync(self, kb_id: ID, version_id: ID) -> list[Chunk]:
        directory = self.version_dir(kb_id, version_id)
        if not _verify_dir(directory, kb_id, version_id):
            raise ResourceGone("snapshot files")
        path = directory / CHUNKS_FILE
        if not path.is_file():
            raise NotFound("chunk file")
        chunks = [
            Chunk.model_validate_json(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if any((chunk.kb_id, chunk.version_id) != (kb_id, version_id) for chunk in chunks):
            raise ValueError("chunk file contains chunks from another snapshot")
        return chunks

    async def load_revision(self, kb_id: ID, version_id: ID, revision_id: ID) -> Revision:
        return await asyncio.to_thread(
            self._load_revision_sync, kb_id, version_id, revision_id
        )

    def _load_revision_sync(self, kb_id: ID, version_id: ID, revision_id: ID) -> Revision:
        directory = self.version_dir(kb_id, version_id)
        if not _verify_dir(directory, kb_id, version_id):
            raise ResourceGone("snapshot files")
        path = directory / REVISION_DIR / f"{_safe(revision_id)}.json"
        if not path.is_file():
            raise NotFound("revision")
        revision = Revision.model_validate_json(path.read_text(encoding="utf-8"))
        if revision.revision_id != revision_id:
            raise ResourceGone("revision files")
        return revision

    def _staging(self, handle: ID) -> Path:
        path = self.root / "staging" / _safe(handle)
        if not path.is_dir():
            raise NotFound("staging handle")
        return path


class PublishedSnapshotReader:
    """The authorized read port A2 consumes; resolves each request once."""

    def __init__(
        self,
        *,
        store: SQLiteStore | None = None,
        files: FileSnapshotStore | None = None,
        knowledge: SQLiteKnowledgeRepository | None = None,
        snapshots: SQLiteSnapshotRepository | None = None,
    ) -> None:
        self._store = store
        self._files = files
        self._knowledge = knowledge or (
            SQLiteKnowledgeRepository(store) if store is not None else None
        )
        self._snapshots = snapshots or (
            SQLiteSnapshotRepository(store) if store is not None else None
        )

    async def resolve(self, kb_id: ID, version_id: ID | None, access: AccessScope) -> Snapshot:
        self._require_wired()
        self._authorize(kb_id, access)
        snapshot = await self._pin(kb_id, version_id)
        await self._require_files(snapshot)
        return snapshot

    async def resolve_many(
        self, targets: list[KBTarget], access: AccessScope
    ) -> ResolvedScope:
        self._require_wired()
        if not targets:
            raise ValueError("at least one target is required")
        if len({target.kb_id for target in targets}) != len(targets):
            raise ValueError("a knowledge base may appear only once")
        scope_id = "scope_" + hashlib.sha256(
            "\0".join(f"{t.kb_id}:{t.version_id or ''}" for t in targets).encode("utf-8")
        ).hexdigest()[:24]
        pinned: list[PinnedKBTarget] = []
        # One read transaction keeps every version pin in a single consistent row set.
        async with self._store.transaction():
            for target in targets:
                self._authorize(target.kb_id, access)
                snapshot = await self._pin(target.kb_id, target.version_id)
                await self._require_files(snapshot)
                pinned.append(
                    PinnedKBTarget(kb_id=snapshot.kb_id, version_id=snapshot.version_id)
                )
        return ResolvedScope(scope_id=scope_id, targets=pinned)

    async def search_scope(self, target: PinnedKBTarget, access: AccessScope) -> SearchScope:
        self._require_wired()
        self._authorize(target.kb_id, access)
        snapshot = await self._pin(target.kb_id, target.version_id)
        await self._require_files(snapshot)
        assert snapshot.keyword_profile and snapshot.keyword_index_ref
        return SearchScope(
            kb_id=snapshot.kb_id,
            version_id=snapshot.version_id,
            scope_id=target.kb_id,
            keyword_profile=snapshot.keyword_profile,
            index_ref=snapshot.keyword_index_ref,
            embedding_profile=snapshot.embedding_profile,
        )

    async def load_chunks(
        self, target: PinnedKBTarget, ids: list[ID], access: AccessScope
    ) -> list[Chunk]:
        self._require_wired()
        self._authorize(target.kb_id, access)
        snapshot = await self._pin(target.kb_id, target.version_id)
        await self._require_files(snapshot)
        return await self._files.load_chunks(target.kb_id, target.version_id, ids)

    async def load_revision(self, revision_id: ID, access: AccessScope) -> Revision:
        row = await self._store.fetchone(
            "SELECT documents.kb_id, revisions.document_id FROM revisions"
            " JOIN documents ON revisions.document_id = documents.document_id"
            " WHERE revisions.revision_id = ?",
            (revision_id,),
        )
        if row is None:
            raise NotFound("revision")
        kb_id = row["kb_id"]
        document_id = row["document_id"]
        self._authorize(kb_id, access)
        # A citation must be read from the immutable snapshot that contains that
        # revision, never from the current document body.
        for snapshot in await self._snapshots.list(kb_id):
            if snapshot.state != SnapshotState.PUBLISHED:
                continue
            if snapshot.document_revisions.get(document_id) != revision_id:
                continue
            await self._require_files(snapshot)
            try:
                return await self._files.load_revision(
                    kb_id, snapshot.version_id, revision_id
                )
            except NotFound:
                continue
        raise ResourceGone("revision files")

    # -- helpers ----------------------------------------------------------
    def _require_wired(self) -> None:
        if self._store is None or self._files is None or self._knowledge is None:
            from qa_contracts.errors import FeatureNotImplemented

            raise FeatureNotImplemented("infrastructure.snapshots.reader")

    @staticmethod
    def _authorize(kb_id: ID, access: AccessScope) -> None:
        if not isinstance(access, AccessScope) or kb_id not in access.kb_ids:
            # Unknown and forbidden look identical: no metadata leak.
            from qa_contracts.errors import PermissionDenied

            raise PermissionDenied("retrieve knowledge base")

    async def _pin(self, kb_id: ID, version_id: ID | None) -> Snapshot:
        if version_id is None:
            kb = await self._knowledge.get(kb_id)
            if not kb.active_version_id:
                raise NotFound("published version")
            version_id = kb.active_version_id
        snapshot = await self._snapshots.get(version_id)
        if snapshot.kb_id != kb_id:
            raise NotFound("version")
        return snapshot

    async def _require_files(self, snapshot: Snapshot) -> None:
        if snapshot.state != SnapshotState.PUBLISHED:
            raise NotFound("published version")
        if not await self._files.verify(snapshot.kb_id, snapshot.version_id):
            raise ResourceGone("snapshot files")


def _safe(value: str) -> str:
    if not value or value != value.replace("/", "_").replace("\\", "_") or value in {".", ".."}:
        raise ValueError("an opaque ID must not contain path separators")
    return value


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _verify_dir(path: Path, kb_id: ID, version_id: ID) -> bool:
    manifest = path / MANIFEST_FILE
    if not manifest.is_file():
        return False
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return False
        if payload.get("kb_id") != kb_id or payload.get("version_id") != version_id:
            return False
        digests = payload.get("digests")
        if not isinstance(digests, dict) or CHUNKS_FILE not in digests:
            return False
        expected_files = {CHUNKS_FILE}
        for candidate in path.rglob("*"):
            if candidate.is_symlink():
                return False
            if candidate.is_file() and candidate != manifest:
                expected_files.add(candidate.relative_to(path).as_posix())
        if set(digests) != expected_files:
            return False
        for relative, expected in digests.items():
            parts = relative.split("/")
            if (
                not parts
                or any(part in {"", ".", ".."} for part in parts)
                or "\\" in relative
                or ":" in relative
                or not isinstance(expected, str)
                or len(expected) != 64
            ):
                return False
            candidate = path.joinpath(*parts)
            if not candidate.is_file() or candidate.is_symlink() or _digest(candidate) != expected:
                return False
        return True
    except (OSError, ValueError, TypeError):
        return False
