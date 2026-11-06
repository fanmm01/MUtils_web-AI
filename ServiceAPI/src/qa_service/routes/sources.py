"""Source-root, source and version routes (A1 owner)."""

from __future__ import annotations

from fastapi import APIRouter

from qa_contracts.errors import ErrorDetail, ValidationFailed
from qa_contracts.knowledge import (
    PublishRequest,
    RollbackRequest,
    Snapshot,
    Source,
    SourceManifest,
    VersionDiff,
)

from ..business import source_root
from ..deps import ContainerDep, services_for

router = APIRouter(tags=["sources"])


@router.get("/v1/source-roots")
async def list_roots(container: ContainerDep) -> list[str]:
    await services_for(container)
    return sorted(container.settings.source_roots)


@router.post("/v1/source-roots/{root_id}/scan", response_model=SourceManifest, status_code=202)
async def scan_source(root_id: str, container: ContainerDep) -> SourceManifest:
    await services_for(container)
    return await source_root(container, root_id).scan()


@router.post("/v1/kbs/{kb_id}/sources", response_model=Source, status_code=201)
async def create_source(kb_id: str, body: Source, container: ContainerDep) -> Source:
    if body.kb_id != kb_id:
        raise ValidationFailed([ErrorDetail(field="kb_id", reason="must match the URL")])
    services = await services_for(container)
    return await services.sources.register(body)


@router.get("/v1/kbs/{kb_id}/sources", response_model=list[Source])
async def list_sources(kb_id: str, container: ContainerDep) -> list[Source]:
    services = await services_for(container)
    return await services.sources.list(kb_id)


@router.get("/v1/sources/{source_id}", response_model=Source)
async def get_source(source_id: str, container: ContainerDep) -> Source:
    services = await services_for(container)
    return await services.sources.get(source_id)


@router.patch("/v1/sources/{source_id}", response_model=Source)
async def update_source(source_id: str, body: Source, container: ContainerDep) -> Source:
    services = await services_for(container)
    return await services.sources.update(source_id, body)


@router.delete("/v1/sources/{source_id}", status_code=204)
async def delete_source(source_id: str, container: ContainerDep) -> None:
    services = await services_for(container)
    await services.sources.remove(source_id)


@router.get("/v1/kbs/{kb_id}/versions", response_model=list[Snapshot])
async def list_versions(kb_id: str, container: ContainerDep) -> list[Snapshot]:
    services = await services_for(container)
    return await services.versions.list(kb_id)


@router.get("/v1/versions/{version_id}", response_model=Snapshot)
async def get_version(version_id: str, container: ContainerDep) -> Snapshot:
    services = await services_for(container)
    return await services.versions.get(version_id)


@router.get("/v1/kbs/{kb_id}/version-diff", response_model=VersionDiff)
async def diff_versions(
    kb_id: str, left: str, right: str, container: ContainerDep
) -> VersionDiff:
    services = await services_for(container)
    difference = await services.versions.diff(left, right)
    versions = await services.versions.list(kb_id)
    version_ids = {snapshot.version_id for snapshot in versions}
    if difference.left not in version_ids:
        raise ValidationFailed(
            [ErrorDetail(field="left", reason="version does not belong to the URL knowledge base")]
        )
    if difference.right not in version_ids:
        raise ValidationFailed(
            [ErrorDetail(field="right", reason="version does not belong to the URL knowledge base")]
        )
    return VersionDiff(
        left=difference.left, right=difference.right,
        added=difference.added, modified=difference.modified, removed=difference.removed,
    )


@router.post("/v1/versions/{version_id}/publish", response_model=Snapshot)
async def publish_version(
    version_id: str, body: PublishRequest, container: ContainerDep
) -> Snapshot:
    services = await services_for(container)
    return await services.versions.publish(version_id, body.expected_active_version_id)


@router.post("/v1/kbs/{kb_id}/rollback", response_model=Snapshot)
async def rollback_version(
    kb_id: str, body: RollbackRequest, container: ContainerDep
) -> Snapshot:
    services = await services_for(container)
    return await services.versions.rollback(
        kb_id, body.target_version_id, body.expected_active_version_id
    )


__all__ = ["router"]
