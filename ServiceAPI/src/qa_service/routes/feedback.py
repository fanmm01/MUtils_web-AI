"""Feedback and issue routes (A2 semantics, A1 route wiring)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from qa_contracts.answers import AskResponse
from qa_contracts.operations import (
    Feedback,
    FeedbackInput,
    Issue,
    IssueQuery,
    IssueResolution,
    RetestRequest,
)

from ..deps import ContainerDep, PrincipalDep
from ..services import not_implemented

router = APIRouter(tags=["feedback"])


@router.post("/v1/answers/{answer_id}/feedback", response_model=Feedback, status_code=201)
async def submit_feedback(
    answer_id: str, body: FeedbackInput, container: ContainerDep, principal: PrincipalDep
) -> Feedback:
    return await not_implemented(container, "feedback", principal, answer_id, body)


@router.get("/v1/issues", response_model=list[Issue])
async def list_issues(
    query: Annotated[IssueQuery, Query()],
    container: ContainerDep,
    principal: PrincipalDep,
) -> list[Issue]:
    return await not_implemented(container, "feedback", principal, query)


@router.get("/v1/issues/{issue_id}", response_model=Issue)
async def get_issue(issue_id: str, container: ContainerDep, principal: PrincipalDep) -> Issue:
    return await not_implemented(container, "feedback", principal, issue_id)


@router.patch("/v1/issues/{issue_id}", response_model=Issue)
async def resolve_issue(
    issue_id: str, body: IssueResolution, container: ContainerDep, principal: PrincipalDep
) -> Issue:
    return await not_implemented(container, "feedback", principal, issue_id, body)


@router.post("/v1/issues/{issue_id}/retest", response_model=AskResponse, status_code=202)
async def retest_issue(
    issue_id: str, body: RetestRequest, container: ContainerDep, principal: PrincipalDep
) -> AskResponse:
    return await not_implemented(container, "feedback", principal, issue_id, body)
