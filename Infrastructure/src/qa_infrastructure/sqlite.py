"""SQLite metadata store: explicit migrations plus an async unit of work.

The store never creates a database file on import or application start. A caller
must run :meth:`SQLiteStore.migrate` (admin action, also exposed as
``qa-migrate``) before :meth:`SQLiteStore.open`.

``sqlite3`` is synchronous; every statement runs in a worker thread while a
single asyncio lock serializes access. A transaction holds that lock for its
whole body (tracked with a context variable so nested repository calls do not
deadlock), which is enough for the single-process course deployment and keeps
read-modify-write sequences honest.
"""

from __future__ import annotations

import asyncio
import sqlite3
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
if not MIGRATIONS_DIR.exists():
    MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"

_INSIDE_TRANSACTION: ContextVar[bool] = ContextVar("qa_sqlite_transaction", default=False)


@dataclass(slots=True)
class MigrationResult:
    applied: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    version: int = 0


class SQLiteStore:
    """One connection, one asynchronous lock, explicit transactions."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self._connection: sqlite3.Connection | None = None
        self._lock: asyncio.Lock | None = None
        self._savepoints: list[str] = []

    # -- lifecycle --------------------------------------------------------
    async def open(self) -> SQLiteStore:
        return await asyncio.to_thread(self._open_sync)

    def _open_sync(self) -> SQLiteStore:
        if self._connection is not None:
            return self
        if not self.database_path.exists():
            raise FileNotFoundError(
                f"{self.database_path} does not exist; run the explicit migration action first"
            )
        connection = sqlite3.connect(
            self.database_path, check_same_thread=False, isolation_level=None
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        self._connection = connection
        return self

    async def close(self) -> None:
        if self._connection is not None:
            await asyncio.to_thread(self._connection.close)
            self._connection = None

    @property
    def opened(self) -> bool:
        return self._connection is not None

    # -- explicit migration (admin action) -------------------------------
    async def migrate(self, target: str = "head") -> MigrationResult:
        return await asyncio.to_thread(self._migrate_sync, target)

    def _migrate_sync(self, target: str) -> MigrationResult:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path, isolation_level=None)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_meta ("
                " version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
            )
            row = connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()
            current = int(row[0] or 0)
            result = MigrationResult(version=current)
            limit = None if target == "head" else int(target)
            for version, path in _migration_files():
                if (limit is not None and version > limit) or version <= current:
                    result.skipped.append(path.name)
                    continue
                script = path.read_text(encoding="utf-8")
                # ``executescript`` commits any open transaction first, so the
                # BEGIN/COMMIT must live inside the same script string.
                script = (
                    "BEGIN IMMEDIATE;\n"
                    f"{script}\n"
                    "INSERT INTO schema_meta (version, applied_at)"
                    f" VALUES ({version}, datetime('now'));\n"
                    "COMMIT;\n"
                )
                try:
                    connection.executescript(script)
                except BaseException:
                    if connection.in_transaction:
                        connection.execute("ROLLBACK")
                    raise
                result.applied.append(path.name)
                result.version = version
            return result
        finally:
            connection.close()

    # -- transaction ------------------------------------------------------
    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[SQLiteStore]:
        """Serialized write transaction; nested use becomes a savepoint."""
        if _INSIDE_TRANSACTION.get():
            savepoint = f"sp_{id(self):x}_{len(self._savepoints)}"
            self._savepoints.append(savepoint)
            await self._statement(f"SAVEPOINT {savepoint}")
            try:
                yield self
            except BaseException:
                await self._statement(f"ROLLBACK TO {savepoint}")
                await self._statement(f"RELEASE {savepoint}")
                self._savepoints.pop()
                raise
            else:
                await self._statement(f"RELEASE {savepoint}")
                self._savepoints.pop()
            return
        lock = self._ensure_lock()
        async with lock:
            await asyncio.to_thread(self._execute, "BEGIN IMMEDIATE")
            token = _INSIDE_TRANSACTION.set(True)
            try:
                yield self
            except BaseException:
                await asyncio.to_thread(self._execute, "ROLLBACK")
                raise
            else:
                await asyncio.to_thread(self._execute, "COMMIT")
            finally:
                _INSIDE_TRANSACTION.reset(token)

    # -- statements -------------------------------------------------------
    async def fetchall(self, sql: str, params: Sequence[Any] = ()) -> list[sqlite3.Row]:
        return await self._run_sync(lambda: self._execute(sql, params).fetchall())

    async def fetchone(self, sql: str, params: Sequence[Any] = ()) -> sqlite3.Row | None:
        rows = await self.fetchall(sql, params)
        return rows[0] if rows else None

    async def execute(self, sql: str, params: Sequence[Any] = ()) -> int:
        return await self._run_sync(lambda: self._execute(sql, params).rowcount or 0)

    async def _statement(self, sql: str) -> None:
        """DDL/top-level transaction control already under the lock."""
        await asyncio.to_thread(self._execute, sql)

    async def _run_sync(self, operation):  # type: ignore[no-untyped-def]
        if _INSIDE_TRANSACTION.get():
            return await asyncio.to_thread(operation)
        lock = self._ensure_lock()
        async with lock:
            return await asyncio.to_thread(operation)

    def _execute(self, sql: str, params: Sequence[Any] = ()) -> sqlite3.Cursor:
        if self._connection is None:
            raise RuntimeError("SQLiteStore is not open")
        return self._connection.execute(sql, tuple(params))

    def _ensure_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock


def _migration_files() -> list[tuple[int, Path]]:
    files: list[tuple[int, Path]] = []
    if not MIGRATIONS_DIR.exists():
        return files
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        prefix = path.name.split("_", 1)[0]
        if prefix.isdigit():
            files.append((int(prefix), path))
    return files
