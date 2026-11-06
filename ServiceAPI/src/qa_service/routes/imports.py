"""Import, upload, source-sync, source-root and version routes (A1 owner)."""

from __future__ import annotations

import tempfile
from typing import Annotated

from fastapi import APIRouter, Header, Request

from qa_contracts.errors import (
    ErrorDetail,
    FeatureNotImplemented,
    PermissionDenied,
    ValidationFailed,
)
from qa_contracts.knowledge import (
    ChangeReceipt,
    ImportPreview,
    ImportPreviewRequest,
    ImportRequest,
    ImportResolution,
    ResolveImportConflicts,
    Selection,
    SourceManifest,
    UploadBatch,
    UploadManifest,
)

from ..deps import ContainerDep, PrincipalDep, services_for

router = APIRouter(tags=["imports"])


def _require_kb(kb_id: str, body_kb_id: str) -> None:
    if kb_id != body_kb_id:
        raise ValidationFailed([ErrorDetail(field="kb_id", reason="must match the URL")])


@router.post("/v1/uploads", response_model=UploadBatch, status_code=202)
async def begin_upload(manifest: UploadManifest, container: ContainerDep) -> UploadBatch:
    services = await services_for(container)
    return await services.uploads.begin(manifest)


@router.put(
    "/v1/uploads/{batch_id}/files",
    status_code=202,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/octet-stream": {
                    "schema": {"type": "string", "format": "binary"}
                }
            },
        }
    },
)
async def upload_file(
    batch_id: str,
    relative_path: str,
    request: Request,
    container: ContainerDep,
) -> None:
    services = await services_for(container)
    max_bytes = services.uploads.max_bytes
    with tempfile.SpooledTemporaryFile(max_size=min(max_bytes, 1024 * 1024), mode="w+b") as payload:
        total = 0
        async for chunk in request.stream():
            total += len(chunk)
            if total > max_bytes:
                raise ValidationFailed(
                    [ErrorDetail(field="file", reason="exceeds the size limit")]
                )
            payload.write(chunk)
        payload.seek(0)
        await services.uploads.write(batch_id, relative_path, payload)


@router.post("/v1/uploads/{batch_id}/complete", response_model=SourceManifest, status_code=202)
async def complete_upload(batch_id: str, container: ContainerDep) -> SourceManifest:
    services = await services_for(container)
    return await services.uploads.finish(batch_id)


@router.post(
    "/v1/kbs/{kb_id}/imports/preview", response_model=ImportPreview, status_code=202
)
async def preview_import(
    kb_id: str, body: ImportPreviewRequest, container: ContainerDep
) -> ImportPreview:
    _require_kb(kb_id, body.kb_id)
    services = await services_for(container)
    manifest = await _manifest_for(services, body)
    return await services.imports.preview(body, manifest)


@router.post(
    "/v1/kbs/{kb_id}/imports/{preview_id}/resolve",
    response_model=ImportResolution,
    status_code=200,
)
async def resolve_import_conflicts(
    kb_id: str,
    preview_id: str,
    body: ResolveImportConflicts,
    container: ContainerDep,
    principal: PrincipalDep,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> ImportResolution:
    """P3 Gate wire contract only; the A1 atomic resolver is not implemented."""
    _require_kb(kb_id, body.kb_id)
    if preview_id != body.preview_id:
        raise ValidationFailed([ErrorDetail(field="preview_id", reason="must match the URL")])
    if not idempotency_key.strip():
        raise ValidationFailed(
            [ErrorDetail(field="Idempotency-Key", reason="must not be empty")]
        )
    if not principal.is_admin:
        raise PermissionDenied("resolve import conflicts")
    del container
    raise FeatureNotImplemented("import conflict resolution")


@router.post("/v1/kbs/{kb_id}/imports", response_model=ChangeReceipt, status_code=202)
async def import_documents(
    kb_id: str, body: ImportRequest, container: ContainerDep
) -> ChangeReceipt:
    _require_kb(kb_id, body.kb_id)
    if body.resolution_id is not None:
        raise FeatureNotImplemented("import conflict resolution")
    services = await services_for(container)
    manifest = await _manifest_for(services, body)
    job = await services.imports.apply(body, manifest)
    return ChangeReceipt(kb_id=kb_id, job_id=job.job_id, requires_publish=True)


@router.post("/v1/sources/{source_id}/sync", response_model=ChangeReceipt, status_code=202)
async def sync_source(
    source_id: str, body: Selection, container: ContainerDep
) -> ChangeReceipt:
    services = await services_for(container)
    source = await services.sources.get(source_id)
    job = await services.imports.sync(source, body)
    return ChangeReceipt(
        kb_id=source.kb_id, job_id=job.job_id, requires_publish=True
    )


async def _manifest_for(services, request) -> SourceManifest:  # type: ignore[no-untyped-def]
    """Server-side scan of the authorized source; clients never send a path."""
    source = await services.sources.get(request.source_id)
    return await services.imports.scan(source, request.selection)


__all__ = ["router"]
