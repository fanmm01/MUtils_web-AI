"""Knowledge-base CRUD routes (A1 owner)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from qa_contracts.base import Page
from qa_contracts.knowledge import CreateKB, KnowledgeBase, PublishRequest, UpdateKB

from ..deps import ContainerDep, PrincipalDep
from ..services import not_implemented

router = APIRouter(prefix="/v1/kbs", tags=["knowledge"])


@router.post("", response_model=KnowledgeBase, status_code=201)
async def create_kb(
    body: CreateKB,
    container: ContainerDep,
    principal: PrincipalDep,
) -> KnowledgeBase:
    return await not_implemented(container, "knowledge", principal, body)


@router.get("", response_model=Page[KnowledgeBase])
async def list_kbs(
    container: ContainerDep,
    principal: PrincipalDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: str | None = None,
) -> Page[KnowledgeBase]:
    return await not_implemented(container, "knowledge", principal, (limit, cursor))


@router.get("/{kb_id}", response_model=KnowledgeBase)
async def get_kb(kb_id: str, container: ContainerDep, principal: PrincipalDep) -> KnowledgeBase:
    return await not_implemented(container, "knowledge", principal, kb_id)


@router.patch("/{kb_id}", response_model=KnowledgeBase)
async def update_kb(
    kb_id: str, body: UpdateKB, container: ContainerDep, principal: PrincipalDep
) -> KnowledgeBase:
    return await not_implemented(container, "knowledge", principal, kb_id, body)


@router.delete("/{kb_id}", status_code=202)
async def delete_kb(
    kb_id: str, container: ContainerDep, principal: PrincipalDep, expected_etag: str | None = None
) -> None:
    return await not_implemented(container, "knowledge", principal, kb_id, expected_etag)


@router.post("/{kb_id}/publish", response_model=KnowledgeBase)
async def publish_kb(
    kb_id: str, body: PublishRequest, container: ContainerDep, principal: PrincipalDep
) -> KnowledgeBase:
    return await not_implemented(container, "versions", principal, kb_id, body)
