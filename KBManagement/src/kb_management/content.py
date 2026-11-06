"""Document and QA-pair content service (A1 owner).

Editing never rewrites history: every change appends an immutable revision and
updates only the document's latest pointer. A QA pair uses the same revision
chain so it can be cited, versioned and indexed like a document.

A change marks the base as "needs a new snapshot". Rebuilding/publishing is a
separate explicit step (``IndexBuilder``) so a failed build never disturbs the
active version.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Protocol

from qa_contracts.base import Page, utc_now
from qa_contracts.errors import (
    Conflict,
    ErrorDetail,
    NotFound,
    ProviderUnavailable,
    ValidationFailed,
)
from qa_contracts.knowledge import (
    ChangeReceipt,
    ContentKind,
    Document,
    DocumentDetail,
    PutDocument,
    PutQA,
    QAPair,
    Revision,
)


class BuildQueue(Protocol):
    """Defers a rebuild; the composition root wires the real job service."""

    async def request_build(self, kb_id: str, *, reason: str) -> str | None: ...


class ContentService:
    def __init__(
        self,
        *,
        content: object,
        qa_pairs: object,
        builds: BuildQueue | None = None,
        store: object | None = None,
    ) -> None:
        self._content = content
        self._qa = qa_pairs
        self._builds = builds
        self._store = store
        if builds is not None and store is None:
            raise ValueError("a synchronous content rebuild requires a transaction store")

    @asynccontextmanager
    async def _transaction(self) -> AsyncIterator[None]:
        if self._store is None:
            yield
        else:
            async with self._store.transaction():
                yield

    # -- documents --------------------------------------------------------
    async def put(self, req: PutDocument, document_id: str | None = None) -> ChangeReceipt:
        async with self._transaction():
            existing = await self._content.find(document_id) if document_id else None
            if document_id and existing is None:
                raise NotFound("document")
            if existing is not None and existing.kb_id != req.kb_id:
                raise ValidationFailed(
                    [ErrorDetail(field="kb_id", reason="does not own this document")]
                )
            if existing is None and req.expected_revision_id is not None:
                raise Conflict(f"revision {req.expected_revision_id}", "no document")
            if existing is not None and req.expected_revision_id is None:
                raise ValidationFailed(
                    [ErrorDetail(field="expected_revision_id", reason="is required to edit")]
                )
            identity = existing.document_id if existing else f"doc_{uuid.uuid4().hex}"
            # Source identity is immutable across manual edits: re-import must
            # match the existing document, not create a duplicate.
            previous_source: str | None = None
            previous_path: str | None = None
            if existing is not None:
                previous = await self._content.latest_revision(identity)
                previous_source = previous.source_id
                previous_path = previous.relative_path
            revision = Revision(
                revision_id=f"rev_{uuid.uuid4().hex}",
                document_id=identity,
                parent_revision_id=existing.latest_revision_id if existing else None,
                content_kind=ContentKind.DOCUMENT,
                source_id=previous_source,
                relative_path=req.relative_path or previous_path,
                normalized_text=req.text,
            )
            await self._content.append_revision(
                identity, revision, req.expected_revision_id,
                kb_id=req.kb_id, title=req.title,
            )
            return await self._receipt(req.kb_id, identity)

    async def get(self, document_id: str, revision_id: str | None = None) -> DocumentDetail:
        detail = await self._content.get(document_id, revision_id)
        if detail.document.content_kind != ContentKind.DOCUMENT:
            raise NotFound("document")
        return detail

    async def list(
        self, kb_id: str, limit: int = 50, cursor: str | None = None
    ) -> Page[Document]:
        return await self._content.list(kb_id, limit, cursor)

    async def delete(self, document_id: str, expected_revision: str | None) -> ChangeReceipt:
        async with self._transaction():
            document = await self._content.find(document_id)
            if document is None or document.content_kind != ContentKind.DOCUMENT:
                raise NotFound("document")
            if expected_revision is None:
                raise ValidationFailed(
                    [ErrorDetail(field="expected_revision_id", reason="is required to delete")]
                )
            await self._content.mark_deleted(document_id, expected_revision)
            return await self._receipt(document.kb_id, document_id)

    # -- QA pairs ---------------------------------------------------------
    async def put_qa(self, req: PutQA, qa_id: str | None = None) -> ChangeReceipt:
        async with self._transaction():
            existing = await self._qa.find(qa_id) if qa_id else None
            if qa_id and (existing is None or existing.deleted):
                raise NotFound("qa pair")
            if existing is not None and existing.kb_id != req.kb_id:
                raise ValidationFailed(
                    [ErrorDetail(field="kb_id", reason="does not own this QA pair")]
                )
            if existing is None and req.expected_revision_id is not None:
                raise Conflict(f"revision {req.expected_revision_id}", "no QA pair")
            if existing is not None and req.expected_revision_id is None:
                raise ValidationFailed(
                    [ErrorDetail(field="expected_revision_id", reason="is required to edit")]
                )
            identity = existing.qa_id if existing else f"qa_{uuid.uuid4().hex}"
            revision = Revision(
                revision_id=f"rev_{uuid.uuid4().hex}",
                document_id=identity,
                parent_revision_id=existing.revision_id if existing else None,
                content_kind=ContentKind.QA_PAIR,
                normalized_text=_qa_text(req.question, req.answer),
            )
            await self._content.append_revision(
                identity, revision, req.expected_revision_id,
                kb_id=req.kb_id, title=req.question[:200],
            )
            await self._qa.put(
                QAPair(
                    qa_id=identity,
                    kb_id=req.kb_id,
                    question=req.question,
                    answer=req.answer,
                    revision_id=revision.revision_id,
                    updated_at=utc_now(),
                ),
                req.expected_revision_id,
            )
            return await self._receipt(req.kb_id, identity)

    async def get_qa(self, qa_id: str) -> QAPair:
        pair = await self._qa.get(qa_id)
        if pair.deleted:
            raise NotFound("qa pair")
        return pair

    async def list_qa(
        self, kb_id: str, limit: int = 50, cursor: str | None = None
    ) -> Page[QAPair]:
        return await self._qa.list(kb_id, limit, cursor)

    async def delete_qa(self, qa_id: str, expected_revision: str | None) -> ChangeReceipt:
        async with self._transaction():
            pair = await self._qa.find(qa_id)
            if pair is None or pair.deleted:
                raise NotFound("qa pair")
            if expected_revision is None:
                raise ValidationFailed(
                    [ErrorDetail(field="expected_revision_id", reason="is required to delete")]
                )
            await self._qa.mark_deleted(qa_id, expected_revision)
            await self._content.mark_deleted(qa_id, expected_revision)
            return await self._receipt(pair.kb_id, qa_id)

    # -- helpers ----------------------------------------------------------
    async def _receipt(self, kb_id: str, document_id: str) -> ChangeReceipt:
        # The rebuild is synchronous in P2-A1 and yields a READY (not active)
        # snapshot. It is reported as ``version_id``, never as a job id, because
        # no background job was enqueued.
        version_id = None
        if self._builds is not None:
            version_id = await self._builds.request_build(kb_id, reason="content change")
            if version_id is None:
                raise ProviderUnavailable("content snapshot could not be built")
        return ChangeReceipt(
            kb_id=kb_id,
            document_id=document_id,
            version_id=version_id,
            requires_publish=True,
        )


def _qa_text(question: str, answer: str) -> str:
    return f"Question: {question}\nAnswer: {answer}"


__all__ = ["BuildQueue", "ContentService"]
