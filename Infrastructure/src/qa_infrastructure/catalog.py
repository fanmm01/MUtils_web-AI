"""Authorized knowledge catalog placeholder.

Reads only authorized, published routing descriptors in later phases; in P1 it
refuses rather than returning an empty catalog (which would read as "no
knowledge bases exist").
"""

from __future__ import annotations

from qa_contracts.base import Page
from qa_contracts.operations import AccessScope
from qa_contracts.selection import CatalogQuery, KBDescriptor

from . import unimplemented


class AuthorizedKnowledgeCatalog:
    async def list_authorized(
        self, access: AccessScope, query: CatalogQuery
    ) -> Page[KBDescriptor]:
        raise unimplemented("infrastructure.catalog.list_authorized")

    async def get_authorized(
        self, access: AccessScope, kb_ids: list[str]
    ) -> list[KBDescriptor]:
        raise unimplemented("infrastructure.catalog.get_authorized")

    async def refresh_descriptor(self, kb_id: str, version_id: str) -> None:
        raise unimplemented("infrastructure.catalog.refresh_descriptor")
