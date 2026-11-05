"""Grounded generation and sentence buffering placeholders."""

from __future__ import annotations

from collections.abc import AsyncIterator

from qa_contracts.answers import DraftFragment, DraftSentence, GenerationRequest
from qa_contracts.errors import FeatureNotImplemented


class GroundedGenerator:
    def __init__(self, *, generator: object) -> None:
        self._generator = generator

    def generate(self, request: GenerationRequest) -> AsyncIterator[DraftSentence]:
        raise FeatureNotImplemented("grounded sentence generation")


class SentenceBuffer:
    """Buffers verified-complete text units without passing through raw tokens."""

    def __init__(self) -> None:
        self._fragments: list[str] = []

    def feed(self, fragment: DraftFragment) -> list[DraftSentence]:
        raise FeatureNotImplemented("sentence boundary buffering")

    def finish(self) -> list[DraftSentence]:
        raise FeatureNotImplemented("sentence buffer finalization")
