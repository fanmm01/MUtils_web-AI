"""Scaffold service stubs.

One place states "this must not work yet": every stub raises
``FeatureNotImplemented``, which the HTTP layer maps to 501. A stub must never
return fake data — that is the difference between an honest scaffold and a
demo that lies to its client.
"""

from __future__ import annotations

from typing import NoReturn, TypeVar

from qa_contracts.errors import FeatureNotImplemented
from qa_contracts.operations import Principal

from .container import Container

T = TypeVar("T")


async def not_implemented(
    container: Container, feature: str, principal: Principal | None = None, *args: object
) -> NoReturn:
    """Reject a business request in the scaffold build.

    ``container``, ``principal`` and ``args`` exist so call sites already have
    the final signature; nothing is read from them.
    """
    del container, principal, args
    raise FeatureNotImplemented(feature)
