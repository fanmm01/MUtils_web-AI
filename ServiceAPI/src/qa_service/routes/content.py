"""Document, QA-pair and revision routes (A1 owner)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from qa_contracts.base import Page
from qa_contracts.errors import ErrorDetail, ValidationFailed
from qa_contracts.knowledge import (
    ChangeReceipt,
    Document,
    DocumentDetail,
    PutDocument,
    PutQA,
    QAPair,
)

from ..deps import ContainerDep, services_for

router = APIRouter(tags=["content"])


def _require_kb(kb_id: str, body_kb_id: str) -> None:
    if kb_id != body_kb_id:
        raise ValidationFailed([ErrorDetail(field="kb_id", reason="must match the URL")])


@router.post("/v1/kbs/{kb_id}/documents", response_model=ChangeReceipt, status_code=202)
async def create_document(
    kb_id: str, body: PutDocument, container: ContainerDep
) -> ChangeReceipt:
    _require_kb(kb_id, body.kb_id)
    services = await services_for(container)
    return await services.content.put(body)


@router.get("/v1/kbs/{kb_id}/documents", response_model=Page[Document])
async def list_documents(
    kb_id: str,
    container: ContainerDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: str | None = None,
) -> Page[Document]:
    services = await services_for(container)
    return await services.content.list(kb_id, limit, cursor)


@router.get("/v1/documents/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: str,
    container: ContainerDep,
    revision_id: str | None = None,
) -> DocumentDetail:
    services = await services_for(container)
    return await services.content.get(document_id, revision_id)


@router.patch("/v1/documents/{document_id}", response_model=ChangeReceipt)
async def update_document(
    document_id: str, body: PutDocument, container: ContainerDep
) -> ChangeReceipt:
    services = await services_for(container)
    return await services.content.put(body, document_id=document_id)


@router.delete("/v1/documents/{document_id}", response_model=ChangeReceipt)
async def delete_document(
    document_id: str,
    container: ContainerDep,
    expected_revision_id: str | None = None,
) -> ChangeReceipt:
    services = await services_for(container)
    return await services.content.delete(document_id, expected_revision_id)


@router.post("/v1/kbs/{kb_id}/qa-pairs", response_model=ChangeReceipt, status_code=202)
async def create_qa(
    kb_id: str, body: PutQA, container: ContainerDep
) -> ChangeReceipt:
    _require_kb(kb_id, body.kb_id)
    services = await services_for(container)
    return await services.content.put_qa(body)


@router.get("/v1/kbs/{kb_id}/qa-pairs", response_model=Page[QAPair])
async def list_qa(
    kb_id: str,
    container: ContainerDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: str | None = None,
) -> Page[QAPair]:
    services = await services_for(container)
    return await services.content.list_qa(kb_id, limit, cursor)


@router.get("/v1/qa-pairs/{qa_id}", response_model=QAPair)
async def get_qa(qa_id: str, container: ContainerDep) -> QAPair:
    services = await services_for(container)
    return await services.content.get_qa(qa_id)


@router.patch("/v1/qa-pairs/{qa_id}", response_model=ChangeReceipt)
async def update_qa(
    qa_id: str, body: PutQA, container: ContainerDep
) -> ChangeReceipt:
    services = await services_for(container)
    return await services.content.put_qa(body, qa_id=qa_id)


@router.delete("/v1/qa-pairs/{qa_id}", response_model=ChangeReceipt)
async def delete_qa(
    qa_id: str,
    container: ContainerDep,
    expected_revision_id: str | None = None,
) -> ChangeReceipt:
    services = await services_for(container)
    return await services.content.delete_qa(qa_id, expected_revision_id)


__all__ = ["router"]
