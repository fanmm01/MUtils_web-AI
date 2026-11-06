"""Knowledge-base CRUD routes (A1 owner).

Route handlers stay thin: validate the DTO (FastAPI), resolve services inside the
handler (so an invalid body is a 422 before any feature gate), then call the
domain service. No business rule lives here.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from qa_contracts.base import Page
from qa_contracts.errors import Conflict
from qa_contracts.knowledge import (
    CreateKB,
    KnowledgeBase,
    PublishRequest,
    SnapshotState,
    UpdateKB,
)

from ..deps import ContainerDep, services_for

router = APIRouter(prefix="/v1/kbs", tags=["knowledge"])


@router.post("", response_model=KnowledgeBase, status_code=201)
async def create_kb(body: CreateKB, container: ContainerDep) -> KnowledgeBase:
    services = await services_for(container)
    return await services.knowledge.create(body)


@router.get("", response_model=Page[KnowledgeBase])
async def list_kbs(
    container: ContainerDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: str | None = None,
) -> Page[KnowledgeBase]:
    services = await services_for(container)
    return await services.knowledge.list(limit, cursor)


@router.get("/{kb_id}", response_model=KnowledgeBase)
async def get_kb(kb_id: str, container: ContainerDep) -> KnowledgeBase:
    services = await services_for(container)
    return await services.knowledge.get(kb_id)


@router.patch("/{kb_id}", response_model=KnowledgeBase)
async def update_kb(
    kb_id: str,
    body: UpdateKB,
    container: ContainerDep,
    expected_etag: str | None = None,
) -> KnowledgeBase:
    services = await services_for(container)
    return await services.knowledge.update(kb_id, body, expected_etag)


@router.delete("/{kb_id}", status_code=202)
async def delete_kb(
    kb_id: str, container: ContainerDep, expected_etag: str | None = None
) -> None:
    services = await services_for(container)
    await services.knowledge.delete(kb_id, expected_etag)


@router.post("/{kb_id}/publish", response_model=KnowledgeBase)
async def publish_kb(
    kb_id: str, body: PublishRequest, container: ContainerDep
) -> KnowledgeBase:
    services = await services_for(container)
    versions = await services.versions.list(kb_id)
    candidates = [
        item for item in versions if item.state == SnapshotState.READY
    ]
    if not candidates:
        raise Conflict("a ready version", "no ready version to publish")
    await services.versions.publish(
        candidates[-1].version_id, body.expected_active_version_id
    )
    return await services.knowledge.get(kb_id)


__all__ = ["router"]
