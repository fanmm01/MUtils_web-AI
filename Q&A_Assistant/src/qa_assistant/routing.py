"""Deterministic selection core placeholders; no routing is performed in P1."""

from __future__ import annotations

from qa_contracts.errors import FeatureNotImplemented
from qa_contracts.models import InferenceBinding
from qa_contracts.operations import AccessScope
from qa_contracts.selection import (
    KBDescriptor,
    PreparedSelection,
    ProbeBudget,
    ProbeResult,
    RankedKB,
    ResolvedScope,
    RetrievalSelection,
    RoutingContext,
    SelectionResult,
)


class KnowledgeRouter:
    """Model-free preparation and binding-aware probe stage placeholder."""

    def __init__(
        self,
        *,
        catalog: object,
        snapshots: object,
        retriever: object,
        reranker: object,
    ) -> None:
        self._catalog = catalog
        self._snapshots = snapshots
        self._retriever = retriever
        self._reranker = reranker

    async def prepare(
        self,
        query: str,
        selection: RetrievalSelection,
        context: RoutingContext,
        access: AccessScope,
    ) -> PreparedSelection:
        raise FeatureNotImplemented("knowledge selection preparation")

    async def select(
        self,
        query: str,
        prepared: PreparedSelection,
        context: RoutingContext,
        binding: InferenceBinding,
    ) -> SelectionResult:
        raise FeatureNotImplemented("knowledge routing")

    async def rank_candidates(
        self,
        query: str,
        descriptors: list[KBDescriptor],
        context: RoutingContext,
    ) -> list[RankedKB]:
        raise FeatureNotImplemented("knowledge candidate ranking")

    async def probe(
        self,
        query: str,
        scope: ResolvedScope,
        budget: ProbeBudget,
        binding: InferenceBinding,
    ) -> list[ProbeResult]:
        raise FeatureNotImplemented("knowledge selection evidence probing")

    def decide(
        self,
        ranked: list[RankedKB],
        probes: list[ProbeResult],
        max_kbs: int,
    ) -> SelectionResult:
        raise FeatureNotImplemented("knowledge selection decision")
