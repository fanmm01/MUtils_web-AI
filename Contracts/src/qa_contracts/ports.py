"""Read ports the domain depends on.

Every port is a ``Protocol`` so neither domain modules nor the API import a
concrete SQLite, file or model implementation. P1 ships placeholders only.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import BinaryIO, Protocol, runtime_checkable

from .answers import AnswerContext, CitationDetail, DraftFragment, Hit, SearchResult
from .base import ID, Page
from .knowledge import (
    Chunk,
    ChunkProfile,
    ParsedDocument,
    Revision,
    SearchScope,
    Snapshot,
    SourceManifest,
    UploadBatch,
    UploadManifest,
)
from .models import EmbeddingProfile, RoleBinding
from .operations import AccessScope
from .selection import CatalogQuery, KBDescriptor, KBTarget, PinnedKBTarget, ResolvedScope

#: One row per input text, in input order.
Vectors = list[list[float]]

#: Token budget accounting value.
TokenCount = int


@runtime_checkable
class KnowledgeCatalog(Protocol):
    async def list_authorized(
        self, access: AccessScope, query: CatalogQuery
    ) -> Page[KBDescriptor]: ...

    async def get_authorized(
        self, access: AccessScope, kb_ids: list[ID]
    ) -> list[KBDescriptor]: ...


@runtime_checkable
class SnapshotReader(Protocol):
    async def resolve(
        self, kb_id: ID, version_id: ID | None, access: AccessScope
    ) -> Snapshot: ...

    async def resolve_many(
        self, targets: list[KBTarget], access: AccessScope
    ) -> ResolvedScope: ...

    async def search_scope(self, target: PinnedKBTarget, access: AccessScope) -> SearchScope: ...

    async def load_chunks(
        self, target: PinnedKBTarget, ids: list[ID], access: AccessScope
    ) -> list[Chunk]: ...

    async def load_revision(self, revision_id: ID, access: AccessScope) -> Revision: ...


@runtime_checkable
class KeywordReader(Protocol):
    async def search(self, query: str, scope: SearchScope, k: int) -> list[Hit]: ...


@runtime_checkable
class VectorReader(Protocol):
    async def search(self, vector: list[float], scope: SearchScope, k: int) -> list[Hit]: ...


@runtime_checkable
class ChunkSplitter(Protocol):
    def split(
        self,
        document: ParsedDocument,
        *,
        kb_id: ID,
        version_id: ID,
        revision_id: ID,
        profile: ChunkProfile,
    ) -> list[Chunk]: ...


@runtime_checkable
class KeywordIndexWriter(Protocol):
    async def build(self, chunks: list[Chunk], profile: str) -> str: ...


@runtime_checkable
class VectorIndexWriter(Protocol):
    async def build(self, vectors: list[list[float]], mapping: list[ID]) -> str: ...


@runtime_checkable
class Embedder(Protocol):
    async def embed(
        self, texts: list[str], profile: EmbeddingProfile, binding: RoleBinding
    ) -> Vectors: ...


@runtime_checkable
class Generator(Protocol):
    def stream(
        self, request: object, binding: RoleBinding
    ) -> AsyncIterator[DraftFragment]: ...


@runtime_checkable
class TokenCounter(Protocol):
    async def count(self, request: object, binding: RoleBinding) -> TokenCount: ...


@runtime_checkable
class SupportChecker(Protocol):
    async def check(self, sentence: str, chunks: list[Chunk], binding: RoleBinding) -> bool: ...


@runtime_checkable
class Reranker(Protocol):
    async def rank(
        self, query: str, hits: list[Hit], binding: RoleBinding
    ) -> list[Hit]: ...


@runtime_checkable
class BlobStore(Protocol):
    async def put(self, stream: BinaryIO) -> str: ...

    async def get(self, ref: str) -> BinaryIO: ...

    async def verify(self, ref: str) -> bool: ...

    async def delete_unreferenced(self, refs: list[str]) -> int: ...


@runtime_checkable
class SnapshotWriter(Protocol):
    async def stage(self, manifest: list[str]) -> ID: ...

    async def seal(self, handle: ID) -> ID: ...


@runtime_checkable
class EmbeddingCache(Protocol):
    async def get_many(self, keys: list[str]) -> dict[str, list[float]]: ...

    async def put_many(self, items: dict[str, list[float]]) -> None: ...


@runtime_checkable
class UploadWriter(Protocol):
    async def begin(self, manifest: UploadManifest) -> UploadBatch: ...

    async def write(self, batch_id: ID, relative_path: str, stream: BinaryIO) -> None: ...

    async def finish(self, batch_id: ID) -> SourceManifest: ...


@runtime_checkable
class Parser(Protocol):
    async def parse(self, stream: BinaryIO, options: object) -> ParsedDocument: ...


@runtime_checkable
class QAServicePort(Protocol):
    """The narrow surface the application layer consumes from the QA core."""

    async def search(
        self, request: object, scope: ResolvedScope, binding: object
    ) -> SearchResult: ...

    def answer(
        self, request: object, context: AnswerContext, scope: ResolvedScope, binding: object
    ) -> AsyncIterator[object]: ...


@runtime_checkable
class CitationResolver(Protocol):
    async def resolve(self, citation_id: ID, scope: ResolvedScope) -> CitationDetail: ...
