"""Evidence guard and citation-resolution placeholders."""

from __future__ import annotations

from qa_contracts.answers import (
    Citation,
    CitationDetail,
    DraftSentence,
    EvidenceDecision,
    Hit,
    VerifiedSentence,
)
from qa_contracts.errors import FeatureNotImplemented
from qa_contracts.knowledge import Chunk
from qa_contracts.models import InferenceBinding
from qa_contracts.selection import ResolvedScope


class EvidenceGuard:
    def __init__(self, *, snapshots: object, support_checker: object) -> None:
        self._snapshots = snapshots
        self._support_checker = support_checker

    async def check_retrieval(
        self, hits: list[Hit], question: str, binding: InferenceBinding
    ) -> EvidenceDecision:
        raise FeatureNotImplemented("evidence sufficiency checking")

    async def validate(
        self,
        sentence: DraftSentence,
        evidence: list[Chunk],
        binding: InferenceBinding,
    ) -> VerifiedSentence:
        raise FeatureNotImplemented("claim and citation validation")

    async def resolve(self, citation: Citation, scope: ResolvedScope) -> CitationDetail:
        raise FeatureNotImplemented("citation detail resolution")

    def refusal(self, reason: str) -> str:
        raise FeatureNotImplemented("grounded refusal generation")
