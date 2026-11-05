"""Application-independent Q&A orchestration facade for the P1 scaffold."""

from __future__ import annotations

from collections.abc import AsyncIterator

from qa_contracts.answers import (
    AnswerContext,
    AnswerEvent,
    SearchRequest,
    SearchResult,
    SubmitAnswer,
)
from qa_contracts.errors import FeatureNotImplemented
from qa_contracts.models import InferenceBinding
from qa_contracts.operations import AccessScope
from qa_contracts.selection import (
    PreparedSelection,
    ResolvedScope,
    RetrievalSelection,
    RoutingContext,
    SelectionResult,
)


class QAService:
    """Typed facade with no HTTP, persistence, model or retrieval side effects."""

    def __init__(
        self,
        *,
        router: object,
        retriever: object,
        context_builder: object,
        evidence_guard: object,
        generator: object,
    ) -> None:
        self._router = router
        self._retriever = retriever
        self._context_builder = context_builder
        self._evidence_guard = evidence_guard
        self._generator = generator

    async def prepare_selection(
        self,
        query: str,
        selection: RetrievalSelection,
        context: RoutingContext,
        access: AccessScope,
    ) -> PreparedSelection:
        raise FeatureNotImplemented("Q&A selection preparation")

    async def select(
        self,
        query: str,
        prepared: PreparedSelection,
        context: RoutingContext,
        binding: InferenceBinding,
    ) -> SelectionResult:
        raise FeatureNotImplemented("Q&A knowledge selection")

    async def search(
        self,
        request: SearchRequest,
        scope: ResolvedScope,
        binding: InferenceBinding,
    ) -> SearchResult:
        raise FeatureNotImplemented("Q&A search")

    def answer(
        self,
        request: SubmitAnswer,
        context: AnswerContext,
        scope: ResolvedScope,
        binding: InferenceBinding,
    ) -> AsyncIterator[AnswerEvent]:
        raise FeatureNotImplemented("grounded Q&A answer generation")
