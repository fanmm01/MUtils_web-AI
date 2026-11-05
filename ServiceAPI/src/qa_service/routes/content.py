"""Document, QA-pair and revision routes (A1 owner)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from qa_contracts.base import Page
from qa_contracts.knowledge import (
    ChangeReceipt,
    Document,
    DocumentDetail,
    PutDocument,
    PutQA,
    QAPair,
)

from ..deps import ContainerDep, PrincipalDep
from ..services import not_implemented

router = APIRouter(tags=["content"])


@router.post("/v1/kbs/{kb_id}/documents", response_model=ChangeReceipt, status_code=202)
async def create_document(
    kb_id: str, body: PutDocument, container: ContainerDep, principal: PrincipalDep
) -> ChangeReceipt:
    return await not_implemented(container, "content", principal, kb_id, body)


@router.get("/v1/kbs/{kb_id}/documents", response_model=Page[Document])
async def list_documents(
    kb_id: str,
    container: ContainerDep,
    principal: PrincipalDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: str | None = None,
) -> Page[Document]:
    return await not_implemented(container, "content", principal, kb_id, limit, cursor)


@router.get("/v1/documents/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: str,
    container: ContainerDep,
    principal: PrincipalDep,
    revision_id: str | None = None,
) -> DocumentDetail:
    return await not_implemented(container, "content", principal, document_id, revision_id)


@router.patch("/v1/documents/{document_id}", response_model=ChangeReceipt)
async def update_document(
    document_id: str, body: PutDocument, container: ContainerDep, principal: PrincipalDep
) -> ChangeReceipt:
    return await not_implemented(container, "content", principal, document_id, body)


@router.delete("/v1/documents/{document_id}", response_model=ChangeReceipt)
async def delete_document(
    document_id: str,
    container: ContainerDep,
    principal: PrincipalDep,
    expected_revision_id: str | None = None,
) -> ChangeReceipt:
    return await not_implemented(container, "content", principal, document_id, expected_revision_id)


@router.post("/v1/kbs/{kb_id}/qa-pairs", response_model=ChangeReceipt, status_code=202)
async def create_qa(
    kb_id: str, body: PutQA, container: ContainerDep, principal: PrincipalDep
) -> ChangeReceipt:
    return await not_implemented(container, "content", principal, kb_id, body)


@router.get("/v1/kbs/{kb_id}/qa-pairs", response_model=Page[QAPair])
async def list_qa(
    kb_id: str,
    container: ContainerDep,
    principal: PrincipalDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: str | None = None,
) -> Page[QAPair]:
    return await not_implemented(container, "content", principal, kb_id, limit, cursor)


@router.get("/v1/qa-pairs/{qa_id}", response_model=QAPair)
async def get_qa(qa_id: str, container: ContainerDep, principal: PrincipalDep) -> QAPair:
    return await not_implemented(container, "content", principal, qa_id)


@router.patch("/v1/qa-pairs/{qa_id}", response_model=ChangeReceipt)
async def update_qa(
    qa_id: str, body: PutQA, container: ContainerDep, principal: PrincipalDep
) -> ChangeReceipt:
    return await not_implemented(container, "content", principal, qa_id, body)


@router.delete("/v1/qa-pairs/{qa_id}", response_model=ChangeReceipt)
async def delete_qa(
    qa_id: str,
    container: ContainerDep,
    principal: PrincipalDep,
    expected_revision_id: str | None = None,
) -> ChangeReceipt:
    return await not_implemented(container, "content", principal, qa_id, expected_revision_id)
