"""SQLite repositories implementing the frozen contract ports.

Each repository maps rows to contract DTOs and enforces optimistic concurrency
with ``expected_*`` comparisons. Business rules (what a change means) live in
``KBManagement``; this module only stores, compares and returns.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any

from qa_contracts.base import ID, Page, utc_now
from qa_contracts.errors import Conflict, NotFound
from qa_contracts.knowledge import (
    BlobRef,
    ContentKind,
    Document,
    DocumentDetail,
    ImportPreview,
    KnowledgeBase,
    QAPair,
    Revision,
    Snapshot,
    SnapshotState,
    Source,
    SourceManifest,
)
from qa_contracts.operations import Job, JobCommand, JobEvent, JobState

from .sqlite import SQLiteStore


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _parse(value: str | None, default: Any) -> Any:
    return json.loads(value) if value else default


def _iso(value: object) -> str | None:
    if value is None:
        return None
    isoformat = getattr(value, "isoformat", None)
    return isoformat() if isoformat else str(value)


def _kb(row: Any) -> KnowledgeBase:
    return KnowledgeBase(
        kb_id=row["kb_id"],
        name=row["name"],
        description=row["description"],
        domain_tags=_parse(row["domain_tags"], []),
        routing_examples=_parse(row["routing_examples"], []),
        active_version_id=row["active_version_id"],
        etag=row["etag"],
        updated_at=row["updated_at"],
    )


def _source(row: Any) -> Source:
    return Source(
        source_id=row["source_id"],
        kb_id=row["kb_id"],
        kind=row["kind"],
        root_id=row["root_id"],
        display_name=row["display_name"],
        revision=row["revision"],
        created_at=row["created_at"],
    )


def _revision(row: Any) -> Revision:
    blob = None
    if row["blob_digest"]:
        blob = BlobRef(
            digest=row["blob_digest"],
            size=int(row["blob_size"] or 0),
            media_type=row["blob_media_type"] or "application/octet-stream",
        )
    return Revision(
        revision_id=row["revision_id"],
        document_id=row["document_id"],
        parent_revision_id=row["parent_revision_id"],
        content_kind=ContentKind(row["content_kind"]),
        source_id=row["source_id"],
        relative_path=row["relative_path"],
        blob=blob,
        normalized_text=row["normalized_text"],
        diagnostics=_parse(row["diagnostics"], []),
        created_at=row["created_at"],
    )


def _document(row: Any) -> Document:
    return Document(
        document_id=row["document_id"],
        kb_id=row["kb_id"],
        title=row["title"],
        latest_revision_id=row["latest_revision_id"],
        content_kind=ContentKind(row["content_kind"]),
        deleted=bool(row["deleted"]),
        updated_at=row["updated_at"],
    )


def _qa(row: Any) -> QAPair:
    return QAPair(
        qa_id=row["qa_id"],
        kb_id=row["kb_id"],
        question=row["question"],
        answer=row["answer"],
        revision_id=row["revision_id"],
        deleted=bool(row["deleted"]),
        updated_at=row["updated_at"],
    )


def _snapshot(row: Any) -> Snapshot:
    return Snapshot(
        version_id=row["version_id"],
        kb_id=row["kb_id"],
        parent_version_id=row["parent_version_id"],
        state=SnapshotState(row["state"]),
        indexed_file_ids=_parse(row["indexed_file_ids"], []),
        document_revisions=_parse(row["document_revisions"], {}),
        keyword_profile=row["keyword_profile"],
        keyword_index_ref=row["keyword_index_ref"],
        embedding_profile=row["embedding_profile"],
        vector_index=row["vector_index"],
        created_at=row["created_at"],
    )


def _job(row: Any) -> Job:
    return Job(
        job_id=row["job_id"],
        kind=row["kind"],
        state=JobState(row["state"]),
        progress=float(row["progress"]),
        revision=int(row["revision"]),
        idempotency_key=row["idempotency_key"],
        lease_until=row["lease_until"],
        worker_id=row["worker_id"] if "worker_id" in row.keys() else None,
        result_version_id=row["result_version_id"],
        diagnostics=_parse(row["diagnostics"], []),
        error_code=row["error_code"],
        created_at=row["created_at"],
    )


class SQLiteKnowledgeRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self._store = store

    async def get(self, kb_id: ID) -> KnowledgeBase:
        row = await self._store.fetchone("SELECT * FROM kbs WHERE kb_id = ?", (kb_id,))
        if row is None:
            raise NotFound("knowledge base")
        return _kb(row)

    async def list(self, limit: int = 50, cursor: str | None = None) -> Page[KnowledgeBase]:
        if limit < 1:
            raise ValueError("limit must be positive")
        rows = await self._store.fetchall(
            "SELECT * FROM kbs WHERE kb_id > ? ORDER BY kb_id LIMIT ?",
            (cursor or "", limit + 1),
        )
        items = [_kb(row) for row in rows[:limit]]
        next_cursor = items[-1].kb_id if len(rows) > limit else None
        return Page(items=items, next_cursor=next_cursor)

    async def create(self, kb: KnowledgeBase) -> KnowledgeBase:
        async with self._store.transaction():
            existing = await self._store.fetchone(
                "SELECT 1 FROM kbs WHERE kb_id = ?", (kb.kb_id,)
            )
            if existing is not None:
                raise Conflict("new knowledge base", f"existing {kb.kb_id}")
            await self._store.execute(
                "INSERT INTO kbs (kb_id, name, description, domain_tags, routing_examples,"
                " active_version_id, etag, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (kb.kb_id, kb.name, kb.description, _json(kb.domain_tags),
                 _json(kb.routing_examples), kb.active_version_id, kb.etag,
                 kb.updated_at.isoformat()),
            )
        return kb

    async def put(self, kb: KnowledgeBase, expected_etag: str | None) -> KnowledgeBase:
        if expected_etag is None:
            return await self.create(kb)
        async with self._store.transaction():
            row = await self._store.fetchone("SELECT etag FROM kbs WHERE kb_id = ?", (kb.kb_id,))
            if row is None:
                raise NotFound("knowledge base")
            if row["etag"] != expected_etag:
                raise Conflict(f"etag {expected_etag}", f"etag {row['etag']}")
            await self._store.execute(
                "UPDATE kbs SET name = ?, description = ?, domain_tags = ?, routing_examples = ?,"
                " active_version_id = ?, etag = ?, updated_at = ? WHERE kb_id = ?",
                (kb.name, kb.description, _json(kb.domain_tags), _json(kb.routing_examples),
                 kb.active_version_id, kb.etag, kb.updated_at.isoformat(), kb.kb_id),
            )
        return kb

    async def delete(self, kb_id: ID, expected_etag: str | None) -> None:
        async with self._store.transaction():
            row = await self._store.fetchone("SELECT etag FROM kbs WHERE kb_id = ?", (kb_id,))
            if row is None:
                raise NotFound("knowledge base")
            if expected_etag is not None and row["etag"] != expected_etag:
                raise Conflict(f"etag {expected_etag}", f"etag {row['etag']}")
            await self._store.execute("DELETE FROM kbs WHERE kb_id = ?", (kb_id,))

    async def all(self) -> list[KnowledgeBase]:
        rows = await self._store.fetchall("SELECT * FROM kbs ORDER BY kb_id")
        return [_kb(row) for row in rows]


class SQLiteSourceRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self._store = store

    async def get(self, source_id: ID) -> Source:
        row = await self._store.fetchone("SELECT * FROM sources WHERE source_id = ?", (source_id,))
        if row is None:
            raise NotFound("source")
        return _source(row)

    async def list(self, kb_id: ID) -> list[Source]:
        rows = await self._store.fetchall(
            "SELECT * FROM sources WHERE kb_id = ? ORDER BY source_id", (kb_id,)
        )
        return [_source(row) for row in rows]

    async def put(self, source: Source, expected_revision: ID | None) -> Source:
        row = await self._store.fetchone(
            "SELECT revision FROM sources WHERE source_id = ?", (source.source_id,)
        )
        if row is None:
            if expected_revision is not None:
                raise NotFound("source")
            await self._store.execute(
                "INSERT INTO sources (source_id, kb_id, kind, root_id, display_name, revision,"
                " created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (source.source_id, source.kb_id, source.kind, source.root_id,
                 source.display_name, source.revision, source.created_at.isoformat()),
            )
            return source
        if expected_revision is not None and row["revision"] != expected_revision:
            raise Conflict(f"revision {expected_revision}", f"revision {row['revision']}")
        await self._store.execute(
            "UPDATE sources SET kind = ?, root_id = ?, display_name = ?, revision = ?"
            " WHERE source_id = ?",
            (source.kind, source.root_id, source.display_name, source.revision, source.source_id),
        )
        return source

    async def remove(self, source_id: ID) -> None:
        deleted = await self._store.execute(
            "DELETE FROM sources WHERE source_id = ?", (source_id,)
        )
        if not deleted:
            raise NotFound("source")

    async def get_manifest(self, source_id: ID, version_id: ID) -> SourceManifest:
        del version_id
        row = await self._store.fetchone(
            "SELECT manifest FROM source_baselines WHERE source_id = ?", (source_id,)
        )
        if row is None:
            raise NotFound("source baseline")
        return SourceManifest.model_validate_json(row["manifest"])

    async def save_manifest(
        self, source_id: ID, version_id: ID, manifest: SourceManifest
    ) -> None:
        del version_id
        await self._store.execute(
            "INSERT INTO source_baselines (source_id, manifest, updated_at)"
            " VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'))"
            " ON CONFLICT(source_id) DO UPDATE SET manifest = excluded.manifest,"
            " updated_at = excluded.updated_at",
            (source_id, manifest.model_dump_json()),
        )

    async def has_baseline(self, source_id: ID) -> bool:
        row = await self._store.fetchone(
            "SELECT 1 FROM source_baselines WHERE source_id = ?", (source_id,)
        )
        return row is not None

    async def get_upload_manifest(self, source_id: ID) -> SourceManifest | None:
        """Latest completed upload batch, exactly as the server verified it."""
        row = await self._store.fetchone(
            "SELECT manifest FROM upload_batches"
            " WHERE source_id = ? AND finished_at IS NOT NULL AND manifest IS NOT NULL"
            " ORDER BY finished_at DESC, batch_id LIMIT 1",
            (source_id,),
        )
        if row is None:
            return None
        return SourceManifest.model_validate_json(row["manifest"])

    async def delete_baseline(self, source_id: ID) -> None:
        await self._store.execute(
            "DELETE FROM source_baselines WHERE source_id = ?", (source_id,)
        )


class SQLiteContentRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self._store = store

    async def get(
        self, document_id: ID, revision_id: ID | None = None
    ) -> DocumentDetail:
        row = await self._store.fetchone(
            "SELECT * FROM documents WHERE document_id = ?", (document_id,)
        )
        if row is None:
            raise NotFound("document")
        document = _document(row)
        wanted = revision_id or document.latest_revision_id
        revision_row = await self._store.fetchone(
            "SELECT * FROM revisions WHERE revision_id = ? AND document_id = ?",
            (wanted, document_id),
        )
        if revision_row is None:
            raise NotFound("revision")
        return DocumentDetail(document=document, revision=_revision(revision_row))

    async def find(self, document_id: ID) -> Document | None:
        row = await self._store.fetchone(
            "SELECT * FROM documents WHERE document_id = ?", (document_id,)
        )
        return _document(row) if row else None

    async def list(
        self, kb_id: ID, limit: int = 50, cursor: str | None = None
    ) -> Page[Document]:
        if limit < 1:
            raise ValueError("limit must be positive")
        rows = await self._store.fetchall(
            "SELECT * FROM documents WHERE kb_id = ? AND deleted = 0 AND document_id > ?"
            " ORDER BY document_id LIMIT ?",
            (kb_id, cursor or "", limit + 1),
        )
        items = [_document(row) for row in rows[:limit]]
        return Page(
            items=items, next_cursor=items[-1].document_id if len(rows) > limit else None
        )

    async def append_revision(
        self,
        document_id: ID,
        revision: Revision,
        expected_revision: ID | None,
        *,
        kb_id: ID,
        title: str,
    ) -> Revision:
        async with self._store.transaction():
            row = await self._store.fetchone(
                "SELECT latest_revision_id FROM documents WHERE document_id = ?", (document_id,)
            )
            if row is None:
                if expected_revision is not None:
                    raise Conflict(f"revision {expected_revision}", "no document")
            elif expected_revision is None:
                raise Conflict("new document", f"existing {document_id}")
            elif row["latest_revision_id"] != expected_revision:
                raise Conflict(
                    f"revision {expected_revision}", f"revision {row['latest_revision_id']}"
                )
            await self._store.execute(
                "INSERT INTO revisions (revision_id, document_id, parent_revision_id,"
                " content_kind, source_id, relative_path, blob_digest, blob_size,"
                " blob_media_type, normalized_text, diagnostics, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (revision.revision_id, document_id, revision.parent_revision_id,
                 revision.content_kind.value, revision.source_id, revision.relative_path,
                 revision.blob.digest if revision.blob else None,
                 revision.blob.size if revision.blob else None,
                 revision.blob.media_type if revision.blob else None,
                 revision.normalized_text, _json(revision.diagnostics),
                 revision.created_at.isoformat()),
            )
            if row is None:
                await self._store.execute(
                    "INSERT INTO documents (document_id, kb_id, title, latest_revision_id,"
                    " content_kind, deleted, updated_at) VALUES (?, ?, ?, ?, ?, 0, ?)",
                    (document_id, kb_id, title, revision.revision_id,
                     revision.content_kind.value, revision.created_at.isoformat()),
                )
            else:
                await self._store.execute(
                    "UPDATE documents SET latest_revision_id = ?, content_kind = ?,"
                    " title = ?, deleted = 0, updated_at = ? WHERE document_id = ?",
                    (revision.revision_id, revision.content_kind.value, title,
                     revision.created_at.isoformat(), document_id),
                )
        return revision

    async def find_by_path(self, source_id: ID, relative_path: str) -> Document | None:
        row = await self._store.fetchone(
            "SELECT documents.* FROM documents JOIN revisions"
            " ON revisions.revision_id = documents.latest_revision_id"
            " WHERE revisions.source_id = ? AND revisions.relative_path = ?",
            (source_id, relative_path),
        )
        return _document(row) if row else None

    async def latest_revision(self, document_id: ID) -> Revision:
        row = await self._store.fetchone(
            "SELECT revisions.* FROM revisions JOIN documents"
            " ON revisions.revision_id = documents.latest_revision_id"
            " WHERE documents.document_id = ?",
            (document_id,),
        )
        if row is None:
            raise NotFound("document")
        return _revision(row)

    async def mark_deleted(self, document_id: ID, expected_revision: ID | None) -> None:
        async with self._store.transaction():
            row = await self._store.fetchone(
                "SELECT latest_revision_id FROM documents WHERE document_id = ?",
                (document_id,),
            )
            if row is None:
                raise NotFound("document")
            if expected_revision is not None and row["latest_revision_id"] != expected_revision:
                raise Conflict(
                    f"revision {expected_revision}", f"revision {row['latest_revision_id']}"
                )
            await self._store.execute(
                "UPDATE documents SET deleted = 1, updated_at ="
                " strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE document_id = ?",
                (document_id,),
            )

    async def list_active_documents(self, kb_id: ID) -> list[Document]:
        rows = await self._store.fetchall(
            "SELECT * FROM documents WHERE kb_id = ? AND deleted = 0 ORDER BY document_id",
            (kb_id,),
        )
        return [_document(row) for row in rows]


class SQLiteQARepository:
    def __init__(self, store: SQLiteStore) -> None:
        self._store = store

    async def get(self, qa_id: ID) -> QAPair:
        row = await self._store.fetchone("SELECT * FROM qa_pairs WHERE qa_id = ?", (qa_id,))
        if row is None:
            raise NotFound("qa pair")
        return _qa(row)

    async def list(self, kb_id: ID, limit: int = 50, cursor: str | None = None) -> Page[QAPair]:
        rows = await self._store.fetchall(
            "SELECT * FROM qa_pairs WHERE kb_id = ? AND deleted = 0 AND qa_id > ?"
            " ORDER BY qa_id LIMIT ?",
            (kb_id, cursor or "", limit + 1),
        )
        items = [_qa(row) for row in rows[:limit]]
        return Page(items=items, next_cursor=items[-1].qa_id if len(rows) > limit else None)

    async def find(self, qa_id: ID) -> QAPair | None:
        row = await self._store.fetchone("SELECT * FROM qa_pairs WHERE qa_id = ?", (qa_id,))
        return _qa(row) if row else None

    async def put(self, pair: QAPair, expected_revision: ID | None) -> QAPair:
        async with self._store.transaction():
            row = await self._store.fetchone(
                "SELECT revision_id FROM qa_pairs WHERE qa_id = ?", (pair.qa_id,)
            )
            if row is None:
                if expected_revision is not None:
                    raise NotFound("qa pair")
                await self._store.execute(
                    "INSERT INTO qa_pairs (qa_id, kb_id, question, answer, revision_id,"
                    " deleted, updated_at) VALUES (?, ?, ?, ?, ?, 0, ?)",
                    (pair.qa_id, pair.kb_id, pair.question, pair.answer, pair.revision_id,
                     pair.updated_at.isoformat()),
                )
                return pair
            if expected_revision is not None and row["revision_id"] != expected_revision:
                raise Conflict(f"revision {expected_revision}", f"revision {row['revision_id']}")
            await self._store.execute(
                "UPDATE qa_pairs SET question = ?, answer = ?, revision_id = ?, deleted = 0,"
                " updated_at = ? WHERE qa_id = ?",
                (pair.question, pair.answer, pair.revision_id, pair.updated_at.isoformat(),
                 pair.qa_id),
            )
        return pair

    async def mark_deleted(self, qa_id: ID, expected_revision: ID | None) -> None:
        async with self._store.transaction():
            row = await self._store.fetchone(
                "SELECT revision_id FROM qa_pairs WHERE qa_id = ?", (qa_id,)
            )
            if row is None:
                raise NotFound("qa pair")
            if expected_revision is not None and row["revision_id"] != expected_revision:
                raise Conflict(f"revision {expected_revision}", f"revision {row['revision_id']}")
            await self._store.execute(
                "UPDATE qa_pairs SET deleted = 1, updated_at ="
                " strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE qa_id = ?",
                (qa_id,),
            )

    async def list_active(self, kb_id: ID) -> list[QAPair]:
        rows = await self._store.fetchall(
            "SELECT * FROM qa_pairs WHERE kb_id = ? AND deleted = 0 ORDER BY qa_id", (kb_id,)
        )
        return [_qa(row) for row in rows]


class SQLiteSnapshotRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self._store = store

    async def get(self, version_id: ID) -> Snapshot:
        row = await self._store.fetchone(
            "SELECT * FROM snapshots WHERE version_id = ?", (version_id,)
        )
        if row is None:
            raise NotFound("version")
        return _snapshot(row)

    async def list(self, kb_id: ID) -> list[Snapshot]:
        rows = await self._store.fetchall(
            "SELECT * FROM snapshots WHERE kb_id = ? ORDER BY created_at, version_id", (kb_id,)
        )
        return [_snapshot(row) for row in rows]

    async def save(self, snapshot: Snapshot) -> None:
        await self._store.execute(
            "INSERT INTO snapshots (version_id, kb_id, parent_version_id, state,"
            " indexed_file_ids, document_revisions, keyword_profile, keyword_index_ref,"
            " embedding_profile, vector_index, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            " ON CONFLICT(version_id) DO UPDATE SET state = excluded.state,"
            " indexed_file_ids = excluded.indexed_file_ids,"
            " document_revisions = excluded.document_revisions,"
            " keyword_profile = excluded.keyword_profile,"
            " keyword_index_ref = excluded.keyword_index_ref,"
            " embedding_profile = excluded.embedding_profile,"
            " vector_index = excluded.vector_index",
            (snapshot.version_id, snapshot.kb_id, snapshot.parent_version_id,
             snapshot.state.value, _json(snapshot.indexed_file_ids),
             _json(snapshot.document_revisions), snapshot.keyword_profile,
             snapshot.keyword_index_ref, snapshot.embedding_profile,
             snapshot.vector_index, snapshot.created_at.isoformat()),
        )

    async def compare_and_swap_active(
        self, kb_id: ID, expected_active: ID | None, target: ID
    ) -> bool:
        async with self._store.transaction():
            row = await self._store.fetchone(
                "SELECT * FROM kbs WHERE kb_id = ?", (kb_id,)
            )
            if row is None:
                raise NotFound("knowledge base")
            if row["active_version_id"] != expected_active:
                return False
            now = utc_now()
            payload = json.dumps(
                [kb_id, row["name"], row["description"], _parse(row["domain_tags"], []),
                 _parse(row["routing_examples"], []), target, now.isoformat()],
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
            etag = hashlib.sha256(payload).hexdigest()
            await self._store.execute(
                "UPDATE kbs SET active_version_id = ?, etag = ?, updated_at = ? WHERE kb_id = ?",
                (target, etag, now.isoformat(), kb_id),
            )
        return True


class SQLiteJobRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self._store = store

    async def enqueue(self, command: JobCommand, key: str) -> Job:
        async with self._store.transaction():
            if command.idempotency_key:
                row = await self._store.fetchone(
                    "SELECT * FROM jobs WHERE kind = ? AND idempotency_key = ?",
                    (command.kind.value, command.idempotency_key),
                )
                if row is not None:
                    return _job(row)
            await self._store.execute(
                "INSERT INTO jobs (job_id, kind, state, progress, revision, idempotency_key,"
                " diagnostics, payload, created_at) VALUES (?, ?, ?, 0, 0, ?, '[]', ?,"
                " strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
                (key, command.kind.value, JobState.QUEUED.value,
                 command.idempotency_key, _json(command.payload)),
            )
            row = await self._store.fetchone("SELECT * FROM jobs WHERE job_id = ?", (key,))
            assert row is not None
            return _job(row)

    async def get(self, job_id: ID) -> Job:
        row = await self._store.fetchone("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        if row is None:
            raise NotFound("job")
        return _job(row)

    async def payload(self, job_id: ID) -> dict[str, object]:
        row = await self._store.fetchone("SELECT payload FROM jobs WHERE job_id = ?", (job_id,))
        if row is None:
            raise NotFound("job")
        return _parse(row["payload"], {})

    async def claim(self, kind: str, worker_id: str, lease_until: object) -> Job | None:
        async with self._store.transaction():
            row = await self._store.fetchone(
                "SELECT * FROM jobs WHERE kind = ? AND state = ?"
                " ORDER BY created_at, job_id LIMIT 1",
                (kind, JobState.QUEUED.value),
            )
            if row is None:
                return None
            await self._store.execute(
                "UPDATE jobs SET state = ?, lease_until = ?, worker_id = ?, revision = revision + 1"
                " WHERE job_id = ? AND state = ?",
                (JobState.RUNNING.value, _iso(lease_until), worker_id, row["job_id"],
                 JobState.QUEUED.value),
            )
            fresh = await self._store.fetchone(
                "SELECT * FROM jobs WHERE job_id = ?", (row["job_id"],)
            )
            return _job(fresh) if fresh else None

    async def renew_lease(self, job_id: ID, worker_id: ID, lease_until: object) -> bool:
        async with self._store.transaction():
            return bool(await self._store.execute(
                "UPDATE jobs SET lease_until = ?, revision = revision + 1"
                " WHERE job_id = ? AND worker_id = ? AND state IN (?, ?)",
                (_iso(lease_until), job_id, worker_id,
                 JobState.RUNNING.value, JobState.CANCEL_REQUESTED.value),
            ))

    async def update(self, job: Job, expected_revision: int) -> Job:
        async with self._store.transaction():
            updated = await self._store.execute(
                "UPDATE jobs SET state = ?, progress = ?, lease_until = ?, worker_id = ?,"
                " result_version_id = ?, diagnostics = ?, error_code = ?,"
                " revision = revision + 1 WHERE job_id = ? AND revision = ?",
                (job.state.value, job.progress, _iso(job.lease_until), job.worker_id,
                 job.result_version_id, _json([d.model_dump() for d in job.diagnostics]),
                 job.error_code, job.job_id, expected_revision),
            )
            if not updated:
                fresh = await self._store.fetchone(
                    "SELECT revision FROM jobs WHERE job_id = ?", (job.job_id,)
                )
                if fresh is None:
                    raise NotFound("job")
                raise Conflict(f"revision {expected_revision}", f"revision {fresh['revision']}")
            row = await self._store.fetchone(
                "SELECT * FROM jobs WHERE job_id = ?", (job.job_id,)
            )
            assert row is not None
            return _job(row)

    async def update_with_event(
        self, job: Job, expected_revision: int, event: JobEvent
    ) -> Job:
        async with self._store.transaction():
            updated = await self._store.execute(
                "UPDATE jobs SET state = ?, progress = ?, lease_until = ?, worker_id = ?,"
                " result_version_id = ?, diagnostics = ?, error_code = ?,"
                " revision = revision + 1 WHERE job_id = ? AND revision = ?",
                (job.state.value, job.progress, _iso(job.lease_until), job.worker_id,
                 job.result_version_id, _json([d.model_dump() for d in job.diagnostics]),
                 job.error_code, job.job_id, expected_revision),
            )
            if not updated:
                fresh = await self._store.fetchone(
                    "SELECT revision FROM jobs WHERE job_id = ?", (job.job_id,)
                )
                if fresh is None:
                    raise NotFound("job")
                raise Conflict(f"revision {expected_revision}", f"revision {fresh['revision']}")
            row = await self._store.fetchone(
                "SELECT COALESCE(MAX(seq), 0) AS seq FROM job_events WHERE job_id = ?",
                (job.job_id,),
            )
            stored = event.model_copy(
                update={"job_id": job.job_id, "seq": int(row["seq"] or 0) + 1}
            )
            await self._store.execute(
                "INSERT INTO job_events (job_id, seq, event) VALUES (?, ?, ?)",
                (job.job_id, stored.seq, stored.model_dump_json()),
            )
            fresh = await self._store.fetchone(
                "SELECT * FROM jobs WHERE job_id = ?", (job.job_id,)
            )
            assert fresh is not None
            return _job(fresh)

    async def recover(self, now: object) -> list[Job]:
        """Recover work whose worker disappeared.

        A RUNNING job whose lease expired goes back to QUEUED. A
        CANCEL_REQUESTED job whose lease expired becomes CANCELLED: the worker
        is gone, and it is no longer honest to say a stop is still pending.
        """
        async with self._store.transaction():
            rows = await self._store.fetchall(
                "SELECT * FROM jobs WHERE state IN (?, ?) AND lease_until IS NOT NULL"
                " AND lease_until < ?",
                (JobState.RUNNING.value, JobState.CANCEL_REQUESTED.value, _iso(now)),
            )
            recovered: list[Job] = []
            for row in rows:
                state = (
                    JobState.CANCELLED
                    if row["state"] == JobState.CANCEL_REQUESTED.value
                    else JobState.QUEUED
                )
                await self._store.execute(
                    "UPDATE jobs SET state = ?, lease_until = NULL, worker_id = NULL,"
                    " revision = revision + 1 WHERE job_id = ?",
                    (state.value, row["job_id"]),
                )
                if state == JobState.CANCELLED:
                    await self._store.execute(
                        "INSERT INTO job_events (job_id, seq, event)"
                        " SELECT ?, COALESCE(MAX(seq), 0) + 1, ? FROM job_events"
                        " WHERE job_id = ?",
                        (
                            row["job_id"],
                            JobEvent(
                                job_id=row["job_id"], seq=1, event="job.cancelled",
                                diagnostic="worker lease expired while cancelling",
                            ).model_dump_json(),
                            row["job_id"],
                        ),
                    )
                fresh = await self._store.fetchone(
                    "SELECT * FROM jobs WHERE job_id = ?", (row["job_id"],)
                )
                if fresh:
                    recovered.append(_job(fresh))
            return recovered

    async def append_event(self, job_id: ID, event: JobEvent) -> JobEvent:
        async with self._store.transaction():
            row = await self._store.fetchone(
                "SELECT MAX(seq) AS seq FROM job_events WHERE job_id = ?", (job_id,)
            )
            seq = int(row["seq"] or 0) + 1
            stored = event.model_copy(update={"job_id": job_id, "seq": seq})
            await self._store.execute(
                "INSERT INTO job_events (job_id, seq, event) VALUES (?, ?, ?)",
                (job_id, seq, stored.model_dump_json()),
            )
            return stored

    async def read_events(self, job_id: ID, after: int, limit: int) -> list[JobEvent]:
        rows = await self._store.fetchall(
            "SELECT event FROM job_events WHERE job_id = ? AND seq > ?"
            " ORDER BY seq LIMIT ?",
            (job_id, after, limit),
        )
        return [JobEvent.model_validate_json(row["event"]) for row in rows]


class SQLiteImportPreviewRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self._store = store

    async def save(
        self,
        preview: ImportPreview,
        manifest: SourceManifest,
        *,
        mode: str,
        baseline_hash: str = "",
    ) -> None:
        await self._store.execute(
            "INSERT INTO import_previews (preview_id, kb_id, source_id, mode, preview_hash,"
            " added, modified, removed, conflicts, manifest, baseline_hash, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            " ON CONFLICT(preview_id) DO UPDATE SET preview_hash = excluded.preview_hash,"
            " baseline_hash = excluded.baseline_hash",
            (preview.preview_id, preview.kb_id, manifest.source_id, mode,
             preview.preview_hash, _json(preview.added), _json(preview.modified),
             _json(preview.removed), _json(preview.conflicts),
             manifest.model_dump_json(), baseline_hash, preview.created_at.isoformat()),
        )

    async def get(self, preview_id: ID) -> tuple[ImportPreview, SourceManifest, str, str]:
        row = await self._store.fetchone(
            "SELECT * FROM import_previews WHERE preview_id = ?", (preview_id,)
        )
        if row is None:
            raise NotFound("import preview")
        return _preview(row)

    async def find(
        self, kb_id: ID, source_id: ID, expected_hash: str
    ) -> tuple[ImportPreview, SourceManifest, str, str] | None:
        """Locate the latest preview matching an apply request's hash."""
        row = await self._store.fetchone(
            "SELECT * FROM import_previews WHERE kb_id = ? AND source_id = ?"
            " AND preview_hash = ? ORDER BY created_at DESC, preview_id LIMIT 1",
            (kb_id, source_id, expected_hash),
        )
        return _preview(row) if row else None


def _preview(row: Any) -> tuple[ImportPreview, SourceManifest, str, str]:
    preview = ImportPreview(
        preview_id=row["preview_id"],
        kb_id=row["kb_id"],
        preview_hash=row["preview_hash"],
        added=_parse(row["added"], []),
        modified=_parse(row["modified"], []),
        removed=_parse(row["removed"], []),
        conflicts=_parse(row["conflicts"], []),
        created_at=row["created_at"],
    )
    manifest = SourceManifest.model_validate_json(row["manifest"])
    keys = row.keys() if hasattr(row, "keys") else []
    baseline = row["baseline_hash"] if "baseline_hash" in keys else ""
    return preview, manifest, row["mode"], baseline or ""


class SQLiteUploadRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self._store = store

    async def begin(
        self, batch_id: ID, source_id: ID, selection: object, files: list[dict[str, object]]
    ) -> None:
        await self._store.execute(
            "INSERT INTO upload_batches (batch_id, source_id, selection, files, created_at)"
            " VALUES (?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
            (batch_id, source_id, _json(selection), _json(files)),
        )

    async def get(self, batch_id: ID) -> dict[str, object]:
        row = await self._store.fetchone(
            "SELECT * FROM upload_batches WHERE batch_id = ?", (batch_id,)
        )
        if row is None:
            raise NotFound("upload batch")
        keys = row.keys()
        return {
            "batch_id": row["batch_id"],
            "source_id": row["source_id"],
            "selection": _parse(row["selection"], {}),
            "files": _parse(row["files"], []),
            "manifest": row["manifest"] if "manifest" in keys else None,
            "finished_at": row["finished_at"],
        }

    async def record_part(
        self, batch_id: ID, relative_path: str, digest: str, size: int
    ) -> None:
        await self._store.execute(
            "INSERT INTO upload_parts (batch_id, relative_path, digest, size)"
            " VALUES (?, ?, ?, ?)"
            " ON CONFLICT(batch_id, relative_path) DO UPDATE SET digest = excluded.digest,"
            " size = excluded.size",
            (batch_id, relative_path, digest, size),
        )

    async def parts(self, batch_id: ID) -> dict[str, tuple[str, int]]:
        rows = await self._store.fetchall(
            "SELECT relative_path, digest, size FROM upload_parts WHERE batch_id = ?",
            (batch_id,),
        )
        return {row["relative_path"]: (row["digest"], int(row["size"])) for row in rows}

    async def finish(self, batch_id: ID, manifest: SourceManifest | None = None) -> None:
        await self._store.execute(
            "UPDATE upload_batches SET finished_at ="
            " strftime('%Y-%m-%dT%H:%M:%fZ','now'), manifest = ? WHERE batch_id = ?",
            (manifest.model_dump_json() if manifest is not None else None, batch_id),
        )


class SQLiteIdempotencyRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self._store = store

    async def claim(
        self, principal_id: ID, operation: str, key: str, request_hash: str, job_id: ID
    ) -> ID | None:
        """Return the original job for a replay; raise when the request changed."""
        async with self._store.transaction():
            row = await self._store.fetchone(
                "SELECT request_hash, job_id FROM idempotency"
                " WHERE principal_id = ? AND operation = ? AND key = ?",
                (principal_id, operation, key),
            )
            if row is not None:
                if row["request_hash"] != request_hash:
                    raise Conflict(
                        f"idempotency key {key} for a different request",
                        f"original request {row['request_hash']}",
                    )
                return str(row["job_id"])
            await self._store.execute(
                "INSERT INTO idempotency (principal_id, operation, key, request_hash, job_id,"
                " created_at) VALUES (?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
                (principal_id, operation, key, request_hash, job_id),
            )
            return None


def sorted_paths(paths: Sequence[str]) -> list[str]:
    return sorted(set(paths))
