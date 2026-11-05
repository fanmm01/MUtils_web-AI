"""Dependency-injection container: the single composition root.

Building the scaffold container must not open a database, probe a runtime, load
a model or touch the network. Every port here is an explicit placeholder, so a
route can be wired and still answer 501 honestly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from qa_contracts.operations import Principal

from .settings import Settings


class PlaceholderPortError(RuntimeError):
    """Raised when placeholder code path is reached; maps to 501 in the API."""


class PrincipalProvider(Protocol):
    def current_principal(self) -> Principal: ...


@dataclass(slots=True)
class Container:
    """Holds settings plus lazily constructible placeholders."""

    settings: Settings
    #: Feature names that the scaffold build must report as unimplemented.
    scaffold_features: tuple[str, ...] = (
        "knowledge",
        "content",
        "imports",
        "sources",
        "versions",
        "search",
        "ask",
        "sessions",
        "feedback",
        "selection",
        "models",
        "jobs",
        "widget",
    )
    _closed: bool = field(default=False, init=False)

    @property
    def mode(self) -> str:
        return self.settings.mode


def build_container(settings: Settings) -> Container:
    """Assemble the container; no I/O, no side effects."""
    return Container(settings=settings)


def close_container(container: Container) -> None:
    """Release resources. Scaffold container owns none."""
    container._closed = True
