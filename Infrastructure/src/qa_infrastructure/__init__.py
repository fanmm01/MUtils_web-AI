"""Infrastructure adapters.

P1 contains typed placeholders that satisfy the contract Protocols by raising
``FeatureNotImplemented``. They must never invent data: a placeholder that
returns an empty list would look like "no knowledge bases exist" and mislead
every client.
"""

from __future__ import annotations

from qa_contracts.errors import FeatureNotImplemented


def unimplemented(component: str) -> FeatureNotImplemented:
    """Uniform rejection for every placeholder adapter method."""
    return FeatureNotImplemented(component)


__all__ = ["unimplemented"]
