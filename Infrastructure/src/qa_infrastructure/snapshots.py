"""Immutable snapshot file store and published-snapshot reader placeholders."""

from __future__ import annotations

from pathlib import Path

from qa_contracts.base import ID
from qa_contracts.knowledge import Chunk, Revision, Snapshot
from qa_contracts.operations import AccessScope
from qa_contracts.selection import KBTarget, ResolvedScope

from . import unimplemented


class FileSnapshotStore:
    """Staging → seal → publish; nothing is written in P1."""

    def __init__(self, root: Path) -> None:
        self.root = root

    async def stage(self, manifest: list[str]) -> ID:
        raise unimplemented("infrastructure.snapshots.stage")

    async def seal(self, handle: ID) -> ID:
        raise unimplemented("infrastructure.snapshots.seal")

    async def open(self, version_id: ID) -> ID:
        raise unimplemented("infrastructure.snapshots.open")

    async def load_chunks(self, version_id: ID, ids: list[ID]) -> list[Chunk]:
        raise unimplemented("infrastructure.snapshots.load_chunks")

    async def load_revision(self, revision_id: ID) -> Revision:
        raise unimplemented("infrastructure.snapshots.load_revision")


class PublishedSnapshotReader:
    """Resolves a whole request's targets in one read transaction (later phase)."""

    async def resolve(self, kb_id: ID, version_id: ID | None) -> Snapshot:
        raise unimplemented("infrastructure.snapshots.resolve")

    async def resolve_many(
        self, targets: list[KBTarget], access: AccessScope
    ) -> ResolvedScope:
        raise unimplemented("infrastructure.snapshots.resolve_many")
