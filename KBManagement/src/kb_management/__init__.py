"""Knowledge-base domain services.

``service.py``, ``content.py``, ``imports.py``, ``sources.py`` and ``versions.py``
are A1-owned; ``chunking.py`` and ``indexing.py`` are A2-owned. The P1 scaffold
declares the entry points and refuses to act.
"""

from __future__ import annotations

from qa_contracts.errors import FeatureNotImplemented


def unimplemented(component: str) -> FeatureNotImplemented:
    return FeatureNotImplemented(component)


__all__ = ["unimplemented"]
