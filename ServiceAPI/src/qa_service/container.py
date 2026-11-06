"""Dependency-injection container: the single composition root.

The container wires real A1 services (SQLite repositories, blob/snapshot stores,
parsers, jobs) and leaves every unimplemented A2 port as an explicit placeholder,
so a route can be wired and still answer 501 honestly.

Opening the database is an *explicit* action: ``build_container`` never creates
or migrates a database. ``open_container`` opens an existing one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from qa_contracts.knowledge import ChunkProfile
from qa_contracts.operations import Principal
from qa_infrastructure.blobs import FileBlobStore
from qa_infrastructure.repositories import (
    SQLiteContentRepository,
    SQLiteIdempotencyRepository,
    SQLiteImportPreviewRepository,
    SQLiteJobRepository,
    SQLiteKnowledgeRepository,
    SQLiteQARepository,
    SQLiteSnapshotRepository,
    SQLiteSourceRepository,
    SQLiteUploadRepository,
)
from qa_infrastructure.snapshots import FileSnapshotStore, PublishedSnapshotReader
from qa_infrastructure.sqlite import SQLiteStore

from .settings import Settings


class PrincipalProvider(Protocol):
    def current_principal(self) -> Principal: ...


@dataclass(slots=True)
class Container:
    """Settings plus lazily constructed services; no I/O until explicitly opened."""

    settings: Settings
    #: Features that still have no real implementation in this build.
    scaffold_features: tuple[str, ...] = (
        "search",
        "ask",
        "sessions",
        "feedback",
        "selection",
        "models",
        "widget",
    )
    #: A1 business features that are implemented when the database is open.
    business_features: tuple[str, ...] = (
        "knowledge",
        "content",
        "imports",
        "sources",
        "versions",
        "jobs",
        "uploads",
    )
    store: SQLiteStore | None = None
    blobs: FileBlobStore | None = None
    snapshot_files: FileSnapshotStore | None = None
    knowledge: SQLiteKnowledgeRepository | None = None
    sources: SQLiteSourceRepository | None = None
    content: SQLiteContentRepository | None = None
    qa_pairs: SQLiteQARepository | None = None
    snapshots: SQLiteSnapshotRepository | None = None
    jobs: SQLiteJobRepository | None = None
    previews: SQLiteImportPreviewRepository | None = None
    uploads: SQLiteUploadRepository | None = None
    idempotency: SQLiteIdempotencyRepository | None = None
    snapshot_reader: PublishedSnapshotReader | None = None
    #: Knowledge bases the local operator may retrieve (published ones).
    authorized_kb_ids: list[str] = field(default_factory=list)
    _closed: bool = field(default=False, init=False)

    @property
    def mode(self) -> str:
        return self.settings.mode

    @property
    def opened(self) -> bool:
        return self.store is not None and self.store.opened


def build_container(settings: Settings) -> Container:
    """Assemble repositories without opening a database or touching the network."""
    container = Container(settings=settings)
    data_dir = settings.data_dir
    container.blobs = FileBlobStore(data_dir / "blobs")
    container.snapshot_files = FileSnapshotStore(data_dir / "snapshots")
    container.store = SQLiteStore(data_dir / "qa.sqlite3")
    return container


async def open_container(container: Container) -> Container:
    """Open an already-migrated database and bind repositories to it."""
    store = container.store
    if store is None:
        raise RuntimeError("container was not built")
    await store.open()
    container.knowledge = SQLiteKnowledgeRepository(store)
    container.sources = SQLiteSourceRepository(store)
    container.content = SQLiteContentRepository(store)
    container.qa_pairs = SQLiteQARepository(store)
    container.snapshots = SQLiteSnapshotRepository(store)
    container.jobs = SQLiteJobRepository(store)
    container.previews = SQLiteImportPreviewRepository(store)
    container.uploads = SQLiteUploadRepository(store)
    container.idempotency = SQLiteIdempotencyRepository(store)
    assert container.snapshot_files is not None
    container.snapshot_reader = PublishedSnapshotReader(
        store=store,
        files=container.snapshot_files,
        knowledge=container.knowledge,
        snapshots=container.snapshots,
    )
    return container


async def migrate_container(container: Container) -> list[str]:
    """Explicit admin action: apply pending migrations and return their names."""
    if container.store is None:
        raise RuntimeError("container was not built")
    result = await container.store.migrate("head")
    return result.applied


def close_container(container: Container) -> None:
    """Release resources synchronously (the API shutdown path)."""
    if container.store is not None and container.store.opened:
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(container.store.close())
        else:
            loop.create_task(container.store.close())
    container._closed = True


__all__ = [
    "ChunkProfile",
    "Container",
    "build_container",
    "close_container",
    "migrate_container",
    "open_container",
]
