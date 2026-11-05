"""Configured model providers placeholder.

``build_provider`` only assembles configured implementations; it performs no
network probe and loads no model. Every role port raises 501 until P3.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from qa_contracts.answers import Hit
from qa_contracts.knowledge import Chunk
from qa_contracts.models import EmbeddingProfile, RoleBinding

from . import unimplemented


class ProviderBundle:
    """Configured implementations for each model role (empty in P1)."""

    def __init__(self, providers: dict[str, object] | None = None) -> None:
        self.providers = providers or {}


class ConfiguredEmbedder:
    async def embed(
        self, texts: list[str], profile: EmbeddingProfile, binding: RoleBinding
    ) -> list[list[float]]:
        raise unimplemented("infrastructure.providers.embed")


class ConfiguredGenerator:
    def stream(self, request: object, binding: RoleBinding) -> AsyncIterator[object]:
        raise unimplemented("infrastructure.providers.stream")


class ConfiguredTokenCounter:
    async def count(self, request: object, binding: RoleBinding) -> int:
        raise unimplemented("infrastructure.providers.count")


class ConfiguredSupportChecker:
    async def check(self, sentence: str, chunks: list[Chunk], binding: RoleBinding) -> bool:
        raise unimplemented("infrastructure.providers.check")


class ConfiguredReranker:
    async def rank(self, query: str, hits: list[Hit], binding: RoleBinding) -> list[Hit]:
        raise unimplemented("infrastructure.providers.rank")


def build_provider(settings: object) -> ProviderBundle:
    """Assemble only configured implementations; never probe or download."""
    del settings
    return ProviderBundle()
