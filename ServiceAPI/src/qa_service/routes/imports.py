"""Import, upload and source-sync routes (A1 owner)."""

from __future__ import annotations

from fastapi import APIRouter, Request

from qa_contracts.knowledge import (
    ChangeReceipt,
    ImportPreview,
    ImportRequest,
    Selection,
    SourceManifest,
)

from ..deps import ContainerDep, PrincipalDep
from ..services import not_implemented

router = APIRouter(tags=["imports"])


@router.post("/v1/uploads", status_code=202)
async def begin_upload(
    container: ContainerDep, principal: PrincipalDep, manifest: SourceManifest
) -> SourceManifest:
    return await not_implemented(container, "imports", principal, manifest)


@router.put("/v1/uploads/{batch_id}/files", status_code=202)
async def upload_file(
    batch_id: str, relative_path: str, request: Request, container: ContainerDep,
    principal: PrincipalDep,
) -> None:
    # The body is never read: no bytes are written in the scaffold.
    return await not_implemented(container, "imports", principal, batch_id, relative_path)


@router.post("/v1/uploads/{batch_id}/complete", response_model=SourceManifest, status_code=202)
async def complete_upload(
    batch_id: str, container: ContainerDep, principal: PrincipalDep
) -> SourceManifest:
    return await not_implemented(container, "imports", principal, batch_id)


@router.post(
    "/v1/kbs/{kb_id}/imports/preview", response_model=ImportPreview, status_code=202
)
async def preview_import(
    kb_id: str, body: ImportRequest, container: ContainerDep, principal: PrincipalDep
) -> ImportPreview:
    return await not_implemented(container, "imports", principal, kb_id, body)


@router.post("/v1/kbs/{kb_id}/imports", response_model=ChangeReceipt, status_code=202)
async def import_documents(
    kb_id: str, body: ImportRequest, container: ContainerDep, principal: PrincipalDep
) -> ChangeReceipt:
    return await not_implemented(container, "imports", principal, kb_id, body)


@router.post("/v1/sources/{source_id}/sync", response_model=ChangeReceipt, status_code=202)
async def sync_source(
    source_id: str,
    body: Selection,
    container: ContainerDep,
    principal: PrincipalDep,
) -> ChangeReceipt:
    return await not_implemented(container, "imports", principal, source_id, body)
