"""Per-KB hybrid retrieval and federation placeholders."""

from __future__ import annotations

from qa_contracts.answers import Hit
from qa_contracts.errors import FeatureNotImplemented
from qa_contracts.models import InferenceBinding
from qa_contracts.selection import ProfileGroup, ResolvedScope


class HybridRetriever:
    """Keyword/vector fusion surface; P1 does not return fabricated hits."""

    def __init__(
        self,
        *,
        keyword_reader: object,
        vector_reader: object,
        embedder: object,
        reranker: object | None = None,
    ) -> None:
        self._keyword_reader = keyword_reader
        self._vector_reader = vector_reader
        self._embedder = embedder
        self._reranker = reranker

    async def retrieve(
        self,
        query: str,
        scope: ResolvedScope,
        binding: InferenceBinding,
        k: int = 10,
    ) -> list[Hit]:
        raise FeatureNotImplemented("hybrid retrieval")

    def fuse(self, keyword: list[Hit], semantic: list[Hit]) -> list[Hit]:
        raise FeatureNotImplemented("hybrid rank fusion")

    def deduplicate(self, hits: list[Hit]) -> list[Hit]:
        raise FeatureNotImplemented("retrieval deduplication")

    async def rerank(self, query: str, hits: list[Hit], binding: InferenceBinding) -> list[Hit]:
        raise FeatureNotImplemented("retrieval reranking")


class FederatedRetriever:
    """Cross-KB retrieval surface; P1 never silently drops a target."""

    def __init__(self, *, retriever: HybridRetriever, embedder: object, reranker: object) -> None:
        self._retriever = retriever
        self._embedder = embedder
        self._reranker = reranker

    async def retrieve(
        self, query: str, scope: ResolvedScope, binding: InferenceBinding
    ) -> list[Hit]:
        raise FeatureNotImplemented("federated retrieval")

    def group_profiles(self, scope: ResolvedScope) -> list[ProfileGroup]:
        raise FeatureNotImplemented("embedding profile grouping")

    async def merge(
        self,
        query: str,
        per_kb: dict[str, list[Hit]],
        k: int,
        binding: InferenceBinding,
    ) -> list[Hit]:
        raise FeatureNotImplemented("federated result merging")

    def deduplicate_preserving_sources(self, hits: list[Hit]) -> list[Hit]:
        raise FeatureNotImplemented("cross-KB provenance-preserving deduplication")
