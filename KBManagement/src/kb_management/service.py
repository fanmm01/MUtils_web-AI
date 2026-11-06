"""Knowledge-base lifecycle: create, read, update, delete.

The active version pointer is only ever moved by the version service; this
service changes metadata and refuses to delete a base that still serves a
published version.
"""

from __future__ import annotations

import hashlib
import json
import uuid

from qa_contracts.base import Page, utc_now
from qa_contracts.errors import Conflict, NotFound
from qa_contracts.knowledge import CreateKB, KnowledgeBase, UpdateKB


def etag_for(kb: KnowledgeBase) -> str:
    payload = json.dumps(
        [kb.kb_id, kb.name, kb.description, kb.domain_tags, kb.routing_examples,
         kb.active_version_id, kb.updated_at.isoformat()],
        ensure_ascii=False, sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class KBService:
    def __init__(
        self,
        *,
        knowledge: object,
        sources: object | None = None,
        content: object | None = None,
        qa_pairs: object | None = None,
        snapshots: object | None = None,
    ) -> None:
        self._knowledge = knowledge
        self._sources = sources
        self._content = content
        self._qa_pairs = qa_pairs
        self._snapshots = snapshots

    async def create(self, req: CreateKB) -> KnowledgeBase:
        now = utc_now()
        kb = KnowledgeBase(
            kb_id=f"kb_{uuid.uuid4().hex}",
            name=req.name,
            description=req.description,
            domain_tags=list(req.domain_tags),
            routing_examples=list(req.routing_examples),
            active_version_id=None,
            etag="",
            updated_at=now,
        )
        return await self._knowledge.create(kb.model_copy(update={"etag": etag_for(kb)}))

    async def get(self, kb_id: str) -> KnowledgeBase:
        return await self._knowledge.get(kb_id)

    async def list(self, limit: int = 50, cursor: str | None = None) -> Page[KnowledgeBase]:
        return await self._knowledge.list(limit, cursor)

    async def update(
        self, kb_id: str, req: UpdateKB, expected_etag: str | None
    ) -> KnowledgeBase:
        current = await self._knowledge.get(kb_id)
        updated = current.model_copy(
            update={
                "name": req.name if req.name is not None else current.name,
                "description": (
                    req.description if req.description is not None else current.description
                ),
                "domain_tags": (
                    list(req.domain_tags) if req.domain_tags is not None
                    else current.domain_tags
                ),
                "routing_examples": (
                    list(req.routing_examples) if req.routing_examples is not None
                    else current.routing_examples
                ),
                "updated_at": utc_now(),
            }
        )
        updated = updated.model_copy(update={"etag": etag_for(updated)})
        return await self._knowledge.put(updated, expected_etag or current.etag)

    async def delete(self, kb_id: str, expected_etag: str | None) -> None:
        """Delete only a base with no served version and no stored content.

        There is no cascade in the schema: deleting rows out from under sources,
        documents, QA pairs or snapshots would strand them (or silently destroy
        them). The operator must remove those first, explicitly.
        """
        current = await self._knowledge.get(kb_id)
        if current.active_version_id:
            raise Conflict(
                "knowledge base without an active version",
                f"active version {current.active_version_id}",
            )
        await self._require_empty(current)
        await self._knowledge.delete(kb_id, expected_etag)

    async def _require_empty(self, kb: KnowledgeBase) -> None:
        if self._sources is not None and await self._sources.list(kb.kb_id):
            raise Conflict("a knowledge base without sources", "sources still exist")
        if self._content is not None and await self._content.list(kb.kb_id, 1):
            page = await self._content.list(kb.kb_id, 1)
            if page.items:
                raise Conflict("a knowledge base without documents", "documents still exist")
        if self._qa_pairs is not None:
            page = await self._qa_pairs.list(kb.kb_id, 1)
            if page.items:
                raise Conflict("a knowledge base without QA pairs", "QA pairs still exist")
        if self._snapshots is not None and await self._snapshots.list(kb.kb_id):
            raise Conflict("a knowledge base without versions", "versions still exist")

    async def require_catalog_visible(self, kb_id: str) -> KnowledgeBase:
        kb = await self._knowledge.get(kb_id)
        if not kb.active_version_id:
            raise NotFound("published knowledge base")
        return kb


__all__ = ["KBService", "etag_for"]
