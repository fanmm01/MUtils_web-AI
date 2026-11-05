"""Document and QA-pair content service placeholder (A1 owner).

Binary replacement or normalized-text edits create a new revision; the original
Word file is never pretended to be rewritten in place.
"""

from __future__ import annotations

from qa_contracts.base import Page
from qa_contracts.knowledge import (
    ChangeReceipt,
    Document,
    DocumentDetail,
    PutDocument,
    PutQA,
    QAPair,
)

from . import unimplemented


class ContentService:
    async def put(self, req: PutDocument) -> ChangeReceipt:
        raise unimplemented("kb.content.put")

    async def get(self, document_id: str, revision_id: str | None = None) -> DocumentDetail:
        raise unimplemented("kb.content.get")

    async def list(self, limit: int = 50, cursor: str | None = None) -> Page[Document]:
        raise unimplemented("kb.content.list")

    async def delete(self, document_id: str, expected_revision: str | None) -> ChangeReceipt:
        raise unimplemented("kb.content.delete")

    async def put_qa(self, req: PutQA) -> ChangeReceipt:
        raise unimplemented("kb.content.put_qa")

    async def get_qa(self, qa_id: str) -> QAPair:
        raise unimplemented("kb.content.get_qa")

    async def list_qa(
        self, kb_id: str, limit: int = 50, cursor: str | None = None
    ) -> Page[QAPair]:
        raise unimplemented("kb.content.list_qa")

    async def delete_qa(self, qa_id: str, expected_revision: str | None) -> ChangeReceipt:
        raise unimplemented("kb.content.delete_qa")
