"""Conversation context preparation placeholders."""

from __future__ import annotations

from qa_contracts.answers import AnswerContext, Hit, Turn
from qa_contracts.errors import FeatureNotImplemented
from qa_contracts.models import InferenceBinding
from qa_contracts.operations import AccessScope
from qa_contracts.selection import HistoryPolicy, ResolvedScope, RoutingContext


class ContextBuilder:
    def __init__(self, *, token_counter: object, rewriter: object | None = None) -> None:
        self._token_counter = token_counter
        self._rewriter = rewriter

    async def bound(
        self, turns: list[Turn], budget: int, binding: InferenceBinding
    ) -> list[Turn]:
        raise FeatureNotImplemented("conversation context budgeting")

    def routing_context(
        self,
        question: str,
        turns: list[Turn],
        history_policy: HistoryPolicy,
        access: AccessScope,
    ) -> RoutingContext:
        raise FeatureNotImplemented("authorized routing context extraction")

    def filter_for_scope(
        self, turns: list[Turn], scope: ResolvedScope, policy: HistoryPolicy
    ) -> list[Turn]:
        raise FeatureNotImplemented("scope-aware conversation history filtering")

    async def rewrite(
        self, question: str, turns: list[Turn], binding: InferenceBinding
    ) -> str:
        raise FeatureNotImplemented("query rewriting")

    async def build(
        self,
        question: str,
        hits: list[Hit],
        turns: list[Turn],
        scope: ResolvedScope,
        binding: InferenceBinding,
    ) -> AnswerContext:
        raise FeatureNotImplemented("bounded answer context construction")
