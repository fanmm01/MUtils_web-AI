"""Knowledge-base lifecycle service placeholder (A1 owner)."""

from __future__ import annotations

from qa_contracts.base import Page
from qa_contracts.knowledge import CreateKB, KnowledgeBase, UpdateKB
from qa_contracts.operations import Job

from . import unimplemented


class KBService:
    async def create(self, req: CreateKB) -> KnowledgeBase:
        raise unimplemented("kb.service.create")

    async def get(self, kb_id: str) -> KnowledgeBase:
        raise unimplemented("kb.service.get")

    async def list(self, limit: int = 50, cursor: str | None = None) -> Page[KnowledgeBase]:
        raise unimplemented("kb.service.list")

    async def update(
        self, kb_id: str, req: UpdateKB, expected_etag: str | None
    ) -> KnowledgeBase:
        raise unimplemented("kb.service.update")

    async def delete(self, kb_id: str, expected_etag: str | None) -> Job:
        raise unimplemented("kb.service.delete")
