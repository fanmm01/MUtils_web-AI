"""Shared A1 integration fixtures: a temporary SQLite store and data directories.

Nothing here talks to the network or loads a model; every test builds its own
temporary database via the explicit migration action, exactly like production.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from qa_contracts.operations import AccessScope
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
from qa_service.app import create_app
from qa_service.settings import ChunkingSettings, Settings


@pytest_asyncio.fixture()
async def store(tmp_path: Path) -> AsyncIterator[SQLiteStore]:
    database = tmp_path / "var" / "qa.sqlite3"
    migrated = SQLiteStore(database)
    await migrated.migrate("head")
    await migrated.close()
    opened = SQLiteStore(database)
    await opened.open()
    try:
        yield opened
    finally:
        await opened.close()


@pytest.fixture()
def knowledge(store: SQLiteStore) -> SQLiteKnowledgeRepository:
    return SQLiteKnowledgeRepository(store)


@pytest.fixture()
def sources(store: SQLiteStore) -> SQLiteSourceRepository:
    return SQLiteSourceRepository(store)


@pytest.fixture()
def content(store: SQLiteStore) -> SQLiteContentRepository:
    return SQLiteContentRepository(store)


@pytest.fixture()
def qa_pairs(store: SQLiteStore) -> SQLiteQARepository:
    return SQLiteQARepository(store)


@pytest.fixture()
def snapshots(store: SQLiteStore) -> SQLiteSnapshotRepository:
    return SQLiteSnapshotRepository(store)


@pytest.fixture()
def jobs(store: SQLiteStore) -> SQLiteJobRepository:
    return SQLiteJobRepository(store)


@pytest.fixture()
def previews(store: SQLiteStore) -> SQLiteImportPreviewRepository:
    return SQLiteImportPreviewRepository(store)


@pytest.fixture()
def uploads(store: SQLiteStore) -> SQLiteUploadRepository:
    return SQLiteUploadRepository(store)


@pytest.fixture()
def idempotency(store: SQLiteStore) -> SQLiteIdempotencyRepository:
    return SQLiteIdempotencyRepository(store)


@pytest.fixture()
def blobs(tmp_path: Path) -> FileBlobStore:
    return FileBlobStore(tmp_path / "var" / "blobs")


@pytest.fixture()
def snapshot_files(tmp_path: Path) -> FileSnapshotStore:
    return FileSnapshotStore(tmp_path / "var" / "snapshots")


@pytest.fixture()
def snapshot_reader(
    store: SQLiteStore,
    snapshot_files: FileSnapshotStore,
) -> PublishedSnapshotReader:
    return PublishedSnapshotReader(store=store, files=snapshot_files)


@pytest.fixture()
def access() -> AccessScope:
    return AccessScope(principal_id="tester", kb_ids=["kb1"], can_manage_kb=True)


@pytest.fixture()
def api(tmp_path: Path) -> Iterator[TestClient]:
    """Operational-mode app over a freshly migrated temporary database."""
    database = tmp_path / "var" / "qa.sqlite3"
    asyncio.run(SQLiteStore(database).migrate("head"))
    settings = Settings(
        mode="operational",
        data_dir=tmp_path / "var",
        chunking=ChunkingSettings(target_tokens=120, overlap_tokens=20),
    )
    app = create_app(settings)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
