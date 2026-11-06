"""Live, authorized routing descriptors supplied by an injected KB metadata reader."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from qa_contracts.base import Page
from qa_contracts.errors import FeatureNotImplemented, PermissionDenied, ValidationFailed
from qa_contracts.knowledge import KnowledgeBase
from qa_contracts.operations import AccessScope
from qa_contracts.selection import CatalogQuery, KBDescriptor


class AuthorizedKnowledgeCatalog:
    """Never exposes source paths, unpublished bases or another principal's metadata.

    The source is the A1-owned metadata read port. Calling it on every request
    avoids a stale catalog after a publish/rollback; no SQLite is imported.
    """

    def __init__(self, source: Callable[[], Awaitable[list[KnowledgeBase]]] | None = None) -> None:
        self._source = source

    async def _published(self, access: AccessScope) -> list[KnowledgeBase]:
        if self._source is None:
            raise FeatureNotImplemented("infrastructure.catalog.source")
        allowed = set(access.kb_ids)
        return sorted(
            (kb for kb in await self._source() if kb.kb_id in allowed and kb.active_version_id),
            key=lambda kb: kb.kb_id,
        )

    @staticmethod
    def _descriptor(kb: KnowledgeBase) -> KBDescriptor:
        return KBDescriptor(
            kb_id=kb.kb_id,
            name=kb.name,
            description=kb.description,
            domain_tags=kb.domain_tags,
            routing_examples=kb.routing_examples,
            version_id=kb.active_version_id,
        )

    async def list_authorized(self, access: AccessScope, query: CatalogQuery) -> Page[KBDescriptor]:
        if self._source is None:
            raise FeatureNotImplemented("infrastructure.catalog.source")
        if not isinstance(access, AccessScope) or not isinstance(query, CatalogQuery):
            raise ValidationFailed()
        search = (query.search or "").casefold().strip()
        rows = [
            kb
            for kb in await self._published(access)
            if (
                not search
                or search
                in " ".join(
                    [kb.name, kb.description, *kb.domain_tags, *kb.routing_examples]
                ).casefold()
            )
            and (query.cursor is None or kb.kb_id > query.cursor)
        ]
        selected = rows[: query.limit]
        return Page(
            items=[self._descriptor(kb) for kb in selected],
            next_cursor=selected[-1].kb_id if len(rows) > query.limit else None,
        )

    async def get_authorized(self, access: AccessScope, kb_ids: list[str]) -> list[KBDescriptor]:
        if self._source is None:
            raise FeatureNotImplemented("infrastructure.catalog.source")
        if not isinstance(access, AccessScope) or not kb_ids or len(kb_ids) != len(set(kb_ids)):
            raise ValidationFailed()
        rows = {kb.kb_id: kb for kb in await self._published(access)}
        if any(kb_id not in rows for kb_id in kb_ids):
            # A caller must not distinguish an unknown, unpublished or forbidden KB.
            raise PermissionDenied("retrieve knowledge base")
        return [self._descriptor(rows[kb_id]) for kb_id in kb_ids]

    async def refresh_descriptor(self, kb_id: str, version_id: str) -> None:
        """The catalog reads live metadata; no cache can go stale on publication."""
        if self._source is None:
            raise FeatureNotImplemented("infrastructure.catalog.source")
        if not kb_id or not version_id:
            raise ValidationFailed()
