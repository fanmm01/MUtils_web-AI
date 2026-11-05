"""FastAPI dependencies shared by every A1 route module."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request, Response

from qa_contracts.operations import AccessScope, Principal

from .container import Container


def get_container(request: Request) -> Container:
    return request.app.state.container  # type: ignore[no-any-return]


ContainerDep = Annotated[Container, Depends(get_container)]


def get_principal(request: Request) -> Principal:
    """Scaffold identity.

    No credentials are validated in P1 and no business route can succeed, so
    this must never be mistaken for authentication. It exists so handlers have
    the right shape for P2.
    """
    return Principal(principal_id="scaffold-anonymous", display_name="scaffold", is_admin=False)


PrincipalDep = Annotated[Principal, Depends(get_principal)]


def scaffold_scope() -> AccessScope:
    return AccessScope(principal_id="scaffold-anonymous")


ScopeDep = Annotated[AccessScope, Depends(scaffold_scope)]


def echo_request_id(request: Request, response: Response) -> None:
    """Attach the correlation ID to every response, success or failure."""
    request_id = getattr(request.state, "request_id", "")
    if request_id:
        response.headers["X-Request-ID"] = request_id


class IdempotencyKey(str):
    """Marker type documented for handlers; validation lives in the service."""


def read_idempotency_key(request: Request) -> str | None:
    return request.headers.get("Idempotency-Key")
