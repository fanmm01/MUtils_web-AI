"""Snapshot version routes (A1 owner)."""

from __future__ import annotations

from fastapi import APIRouter

from qa_contracts.knowledge import PublishRequest, RollbackRequest, Snapshot

from ..deps import ContainerDep, PrincipalDep
from ..services import not_implemented

router = APIRouter(tags=["versions"])


@router.get("/v1/kbs/{kb_id}/versions", response_model=list[Snapshot])
async def list_versions(
    kb_id: str, container: ContainerDep, principal: PrincipalDep
) -> list[Snapshot]:
    return await not_implemented(container, "versions", principal, kb_id)


@router.get("/v1/versions/{version_id}", response_model=Snapshot)
async def get_version(
    version_id: str, container: ContainerDep, principal: PrincipalDep
) -> Snapshot:
    return await not_implemented(container, "versions", principal, version_id)


@router.get("/v1/kbs/{kb_id}/version-diff")
async def diff_versions(
    kb_id: str,
    left: str,
    right: str,
    container: ContainerDep,
    principal: PrincipalDep,
) -> dict[str, object]:
    return await not_implemented(container, "versions", principal, kb_id, left, right)


@router.post("/v1/versions/{version_id}/publish", response_model=Snapshot)
async def publish_version(
    version_id: str, body: PublishRequest, container: ContainerDep, principal: PrincipalDep
) -> Snapshot:
    return await not_implemented(container, "versions", principal, version_id, body)


@router.post("/v1/kbs/{kb_id}/rollback", response_model=Snapshot)
async def rollback_version(
    kb_id: str, body: RollbackRequest, container: ContainerDep, principal: PrincipalDep
) -> Snapshot:
    return await not_implemented(container, "versions", principal, kb_id, body)
