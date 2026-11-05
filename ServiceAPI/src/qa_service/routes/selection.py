"""Knowledge catalog and selection preview routes (A2 semantics, A1 wiring)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from qa_contracts.base import Page
from qa_contracts.selection import (
    CatalogQuery,
    KBDescriptor,
    SelectionPreviewRequest,
    SelectionResult,
)

from ..deps import ContainerDep, PrincipalDep
from ..services import not_implemented

router = APIRouter(tags=["selection"])


@router.get("/v1/knowledge-catalog", response_model=Page[KBDescriptor])
async def list_retrievable_kbs(
    query: Annotated[CatalogQuery, Query()],
    container: ContainerDep,
    principal: PrincipalDep,
) -> Page[KBDescriptor]:
    return await not_implemented(container, "selection", principal, query)


@router.post(
    "/v1/knowledge-selection/preview", response_model=SelectionResult, status_code=202
)
async def preview_selection(
    body: SelectionPreviewRequest, container: ContainerDep, principal: PrincipalDep
) -> SelectionResult:
    return await not_implemented(container, "selection", principal, body)
