"""P2 keyword-only retrieval. Vector fusion and model reranking remain P3."""

from __future__ import annotations

import asyncio
import re
import unicodedata

from qa_contracts.answers import Hit
from qa_contracts.errors import FeatureNotImplemented, PermissionDenied
from qa_contracts.knowledge import SearchScope
from qa_contracts.models import InferenceBinding
from qa_contracts.operations import AccessScope
from qa_contracts.ports import Embedder, KeywordReader, Reranker, SnapshotReader, VectorReader
from qa_contracts.selection import ProfileGroup, ResolvedScope

_TERM = re.compile(r"[㐀-鿿]+|[a-z0-9_]+(?:[-./][a-z0-9_]+)*")


def _terms(text: str) -> set[str]:
    result: set[str] = set()
    for match in _TERM.finditer(unicodedata.normalize("NFKC", text).casefold()):
        token = match.group()
        if "㐀" <= token[0] <= "鿿" and len(token) > 1:
            result.update(token[i : i + 2] for i in range(len(token) - 1))
        else:
            result.add(token)
    return result


class HybridRetriever:
    """The P2 path uses only the pinned keyword index, never a model call."""

    def __init__(
        self,
        *,
        keyword_reader: KeywordReader,
        vector_reader: VectorReader | None = None,
        embedder: Embedder | None = None,
        reranker: Reranker | None = None,
    ) -> None:
        self._keyword_reader = keyword_reader
        self._vector_reader = vector_reader
        self._embedder = embedder
        self._reranker = reranker

    async def retrieve(
        self,
        query: str,
        scope: SearchScope,
        binding: InferenceBinding,
        k: int,
    ) -> list[Hit]:
        if k < 1:
            raise ValueError("top_k must be positive")
        if not isinstance(scope, SearchScope) or not hasattr(self._keyword_reader, "search"):
            raise FeatureNotImplemented("hybrid retrieval")
        hits = await self._keyword_reader.search(query, scope, k)
        if any((hit.kb_id, hit.version_id) != (scope.kb_id, scope.version_id) for hit in hits):
            raise ValueError("keyword reader returned a hit outside the pinned snapshot")
        return self.deduplicate(hits)[:k]

    def fuse(self, keyword: list[Hit], semantic: list[Hit]) -> list[Hit]:
        raise FeatureNotImplemented("hybrid rank fusion")

    def deduplicate(self, hits: list[Hit]) -> list[Hit]:
        seen: set[tuple[str, str, str]] = set()
        result = []
        for hit in hits:
            key = (hit.kb_id, hit.version_id, hit.chunk_id)
            if key not in seen:
                result.append(hit)
                seen.add(key)
        return result

    async def rerank(self, query: str, hits: list[Hit], binding: InferenceBinding) -> list[Hit]:
        raise FeatureNotImplemented("retrieval reranking")


class FederatedRetriever:
    """Attempt every explicitly pinned KB; combine ranks, never raw BM25 values."""

    def __init__(
        self,
        *,
        retriever: HybridRetriever,
        snapshots: SnapshotReader,
        embedder: Embedder | None = None,
        reranker: Reranker | None = None,
    ) -> None:
        self._retriever = retriever
        self._snapshots = snapshots
        self._embedder = embedder
        self._reranker = reranker

    async def retrieve(
        self,
        query: str,
        scope: ResolvedScope,
        binding: InferenceBinding,
        k: int,
        *,
        access: AccessScope | None = None,
    ) -> list[Hit]:
        if k < 1:
            raise ValueError("top_k must be positive")
        if not isinstance(scope, ResolvedScope):
            raise FeatureNotImplemented("federated retrieval")
        if access is None:
            raise PermissionDenied("retrieve knowledge base")
        if any(target.kb_id not in access.kb_ids for target in scope.targets):
            raise PermissionDenied("retrieve knowledge base")
        if len(scope.targets) != len({target.kb_id for target in scope.targets}):
            raise ValueError("resolved scope contains duplicate knowledge bases")

        async def _retrieve_target(target):
            search_scope = await self._snapshots.search_scope(target, access)
            if (search_scope.kb_id, search_scope.version_id) != (
                target.kb_id,
                target.version_id,
            ):
                raise ValueError("snapshot reader returned a different pinned version")
            hits = await self._retriever.retrieve(query, search_scope, binding, k)
            if any(
                (hit.kb_id, hit.version_id) != (target.kb_id, target.version_id) for hit in hits
            ):
                raise ValueError("keyword reader returned hits outside the pinned snapshot")
            return target.kb_id, hits

        outcomes = await asyncio.gather(
            *(_retrieve_target(target) for target in scope.targets), return_exceptions=True
        )
        failures = [outcome for outcome in outcomes if isinstance(outcome, BaseException)]
        if failures:
            raise failures[0]
        results = dict(outcome for outcome in outcomes)
        return await self.merge(query, results, k, binding)

    def group_profiles(self, scope: ResolvedScope) -> list[ProfileGroup]:
        raise FeatureNotImplemented("embedding profile grouping")

    async def merge(
        self,
        query: str,
        per_kb: dict[str, list[Hit]],
        k: int,
        binding: InferenceBinding,
    ) -> list[Hit]:
        if k < 1:
            raise ValueError("top_k must be positive")
        terms = _terms(query)
        ranked: list[tuple[float, int, int, Hit]] = []
        for kb_position, (kb_id, hits) in enumerate(per_kb.items()):
            for position, hit in enumerate(hits):
                if hit.kb_id != kb_id:
                    raise ValueError("keyword reader returned a different knowledge base")
                # One common textual coverage scale; raw BM25 values and
                # unrelated per-KB ranks never become cross-KB relevance.
                score = len(terms & _terms(hit.text)) / len(terms) if terms else 0.0
                ranked.append(
                    (score, position, kb_position, hit.model_copy(update={"score": score}))
                )
        ranked.sort(key=lambda row: (-row[0], row[1], row[2], row[3].chunk_id))
        return self.deduplicate_preserving_sources([row[3] for row in ranked])[:k]

    def deduplicate_preserving_sources(self, hits: list[Hit]) -> list[Hit]:
        return self._retriever.deduplicate(hits)
