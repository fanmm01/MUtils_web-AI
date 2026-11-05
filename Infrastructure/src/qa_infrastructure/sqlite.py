"""SQLite store placeholder.

``open`` does not create the database file; migration is an explicit admin
action in a later phase and never runs on import.
"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from pathlib import Path
from typing import Protocol

from qa_contracts.base import Page
from qa_contracts.knowledge import KnowledgeBase, Snapshot
from qa_contracts.models import (
    DiscoveryReport,
    InstallPreview,
    ModelRef,
    ProfileSummary,
    RuntimeStatus,
)
from qa_contracts.operations import AccessScope
from qa_contracts.selection import CatalogQuery, KBDescriptor

from . import unimplemented


class ConnectionPool(Protocol):
    async def close(self) -> None: ...


class MigrationResult(Protocol):
    applied: list[str]
    skipped: list[str]


class SQLiteStore:
    """Placeholder store; holds configuration only, opens nothing."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    async def open(self) -> ConnectionPool:
        raise unimplemented("infrastructure.sqlite.open")

    def transaction(self) -> AbstractAsyncContextManager[object]:
        raise unimplemented("infrastructure.sqlite.transaction")

    async def close(self) -> None:
        raise unimplemented("infrastructure.sqlite.close")

    async def migrate(self, target: str) -> MigrationResult:
        raise unimplemented("infrastructure.sqlite.migrate")


# Side-effect-free placeholders so A2 can import repository types without a DB.
class SQLiteKnowledgeRepository:
    async def get(self, kb_id: str) -> KnowledgeBase:
        raise unimplemented("infrastructure.repositories.knowledge.get")

    async def list(self, limit: int = 50, cursor: str | None = None) -> Page[KnowledgeBase]:
        raise unimplemented("infrastructure.repositories.knowledge.list")


class SQLiteSnapshotRepository:
    async def get(self, version_id: str) -> Snapshot:
        raise unimplemented("infrastructure.repositories.snapshot.get")


class SQLiteCatalog:
    async def list_authorized(
        self, access: AccessScope, query: CatalogQuery
    ) -> Page[KBDescriptor]:
        raise unimplemented("infrastructure.catalog.list_authorized")


class SQLiteModelRepository:
    async def list_runtimes(self) -> list[RuntimeStatus]:
        raise unimplemented("infrastructure.repositories.model.list_runtimes")

    async def save_discovery(self, report: DiscoveryReport) -> None:
        raise unimplemented("infrastructure.repositories.model.save_discovery")

    async def list_models(self, query: object) -> Page[ModelRef]:
        raise unimplemented("infrastructure.repositories.model.list_models")

    async def list_profiles(self, access: AccessScope) -> Page[ProfileSummary]:
        raise unimplemented("infrastructure.repositories.model.list_profiles")

    async def save_preview(self, preview: InstallPreview) -> None:
        raise unimplemented("infrastructure.repositories.model.save_preview")
