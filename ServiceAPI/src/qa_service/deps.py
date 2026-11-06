"""FastAPI dependencies shared by every A1 route module."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request, Response

from qa_contracts.operations import AccessScope, Principal

from .business import BusinessServices, require_services
from .container import Container


def get_container(request: Request) -> Container:
    return request.app.state.container  # type: ignore[no-any-return]


ContainerDep = Annotated[Container, Depends(get_container)]


def get_principal(request: Request) -> Principal:
    """Identity for the single-user deployment.

    P2-A1 still has no credential validation; every business call is restricted
    to the server operator and no request can widen its scope. Authentication is
    a later-phase concern and must not be assumed from this placeholder.
    """
    return Principal(principal_id="local-operator", display_name="local operator", is_admin=True)


PrincipalDep = Annotated[Principal, Depends(get_principal)]


def scaffold_scope(request: Request) -> AccessScope:
    container: Container = request.app.state.container
    return AccessScope(
        principal_id="local-operator",
        kb_ids=list(container.authorized_kb_ids),
        can_manage_kb=True,
        can_manage_models=True,
    )


ScopeDep = Annotated[AccessScope, Depends(scaffold_scope)]


async def services_for(container: Container) -> BusinessServices:
    """A1 services, resolved *inside* a handler.

    It must not run as a FastAPI dependency: a dependency failure would mask
    request-body validation, and an invalid body must be a 422, never a 501.
    501 (scaffold mode) and 503 (no database) are raised after validation.
    """
    return await require_services(container)


def echo_request_id(request: Request, response: Response) -> None:
    """Attach the correlation ID to every response, success or failure."""
    request_id = getattr(request.state, "request_id", "")
    if request_id:
        response.headers["X-Request-ID"] = request_id


class IdempotencyKey(str):
    """Marker type documented for handlers; validation lives in the service."""


def read_idempotency_key(request: Request) -> str | None:
    return request.headers.get("Idempotency-Key")
