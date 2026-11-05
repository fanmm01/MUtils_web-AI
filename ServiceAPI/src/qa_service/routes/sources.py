"""Source-root and source routes (A1 owner)."""

from __future__ import annotations

from fastapi import APIRouter

from qa_contracts.knowledge import Source, SourceManifest

from ..deps import ContainerDep, PrincipalDep
from ..services import not_implemented

router = APIRouter(tags=["sources"])


@router.get("/v1/source-roots")
async def list_roots(container: ContainerDep, principal: PrincipalDep) -> list[str]:
    return await not_implemented(container, "sources", principal)


@router.post("/v1/source-roots/{root_id}/scan", response_model=SourceManifest, status_code=202)
async def scan_source(
    root_id: str, container: ContainerDep, principal: PrincipalDep
) -> SourceManifest:
    return await not_implemented(container, "sources", principal, root_id)


@router.post("/v1/kbs/{kb_id}/sources", response_model=Source, status_code=201)
async def create_source(
    kb_id: str, body: Source, container: ContainerDep, principal: PrincipalDep
) -> Source:
    return await not_implemented(container, "sources", principal, kb_id, body)


@router.get("/v1/kbs/{kb_id}/sources", response_model=list[Source])
async def list_sources(
    kb_id: str, container: ContainerDep, principal: PrincipalDep
) -> list[Source]:
    return await not_implemented(container, "sources", principal, kb_id)


@router.get("/v1/sources/{source_id}", response_model=Source)
async def get_source(
    source_id: str, container: ContainerDep, principal: PrincipalDep
) -> Source:
    return await not_implemented(container, "sources", principal, source_id)


@router.patch("/v1/sources/{source_id}", response_model=Source)
async def update_source(
    source_id: str, body: Source, container: ContainerDep, principal: PrincipalDep
) -> Source:
    return await not_implemented(container, "sources", principal, source_id, body)


@router.delete("/v1/sources/{source_id}", status_code=204)
async def delete_source(
    source_id: str, container: ContainerDep, principal: PrincipalDep
) -> None:
    return await not_implemented(container, "sources", principal, source_id)
