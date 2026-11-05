"""Index and embedding-cache placeholders (BM25, dense index, cache)."""

from __future__ import annotations

from qa_contracts.answers import Hit
from qa_contracts.base import ID
from qa_contracts.knowledge import Chunk, Snapshot

from . import unimplemented


class ChineseTokenizer:
    """Deterministic placeholder: no dictionary is bundled in P1."""

    def tokenize(self, text: str) -> list[str]:
        raise unimplemented("infrastructure.indexes.tokenizer")


class BM25Index:
    async def build(self, chunks: list[Chunk], profile: str) -> str:
        raise unimplemented("infrastructure.indexes.bm25.build")

    async def search(self, query: str, scope: Snapshot, k: int) -> list[Hit]:
        raise unimplemented("infrastructure.indexes.bm25.search")


class DenseIndex:
    async def build(self, vectors: list[list[float]], mapping: list[ID]) -> str:
        raise unimplemented("infrastructure.indexes.dense.build")

    async def search(self, vector: list[float], scope: Snapshot, k: int) -> list[Hit]:
        raise unimplemented("infrastructure.indexes.dense.search")


class EmbeddingCache:
    async def get_many(self, keys: list[str]) -> dict[str, list[float]]:
        raise unimplemented("infrastructure.indexes.cache.get_many")

    async def put_many(self, items: dict[str, list[float]]) -> None:
        raise unimplemented("infrastructure.indexes.cache.put_many")
