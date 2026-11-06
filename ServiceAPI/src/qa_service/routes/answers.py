"""Search, ask, session and answer routes (A2 semantics, A1 route wiring)."""

from __future__ import annotations

from fastapi import APIRouter, Request

from qa_contracts.answers import (
    Answer,
    AskRequest,
    AskResponse,
    CitationDetail,
    CreateSession,
    SearchRequest,
    SearchResult,
    Session,
    SubmitAnswer,
    Turn,
)
from qa_contracts.selection import SessionSelection, UpdateSessionSelection

from ..deps import ContainerDep, PrincipalDep, read_idempotency_key
from ..services import not_implemented

router = APIRouter(tags=["answers"])


@router.post("/v1/search", response_model=SearchResult)
async def search(
    body: SearchRequest, container: ContainerDep, principal: PrincipalDep
) -> SearchResult:
    return await not_implemented(container, "search", principal, body)


@router.post("/v1/ask", response_model=AskResponse)
async def ask(
    body: AskRequest, request: Request, container: ContainerDep, principal: PrincipalDep
) -> AskResponse:
    return await not_implemented(container, "ask", principal, body, read_idempotency_key(request))


@router.post("/v1/sessions", response_model=Session, status_code=201)
async def create_session(
    body: CreateSession, container: ContainerDep, principal: PrincipalDep
) -> Session:
    return await not_implemented(container, "sessions", principal, body)


@router.get("/v1/sessions/{session_id}/history", response_model=list[Turn])
async def history(
    session_id: str, container: ContainerDep, principal: PrincipalDep
) -> list[Turn]:
    return await not_implemented(container, "sessions", principal, session_id)


@router.get("/v1/sessions/{session_id}/selection", response_model=SessionSelection)
async def get_session_selection(
    session_id: str, container: ContainerDep, principal: PrincipalDep
) -> SessionSelection:
    return await not_implemented(container, "selection", principal, session_id)


@router.patch("/v1/sessions/{session_id}/selection", response_model=SessionSelection)
async def update_session_selection(
    session_id: str,
    body: UpdateSessionSelection,
    container: ContainerDep,
    principal: PrincipalDep,
) -> SessionSelection:
    return await not_implemented(container, "selection", principal, session_id, body)


@router.post("/v1/sessions/{session_id}/answers", response_model=AskResponse, status_code=202)
async def submit_answer(
    session_id: str,
    body: SubmitAnswer,
    request: Request,
    container: ContainerDep,
    principal: PrincipalDep,
) -> AskResponse:
    return await not_implemented(
        container, "ask", principal, session_id, body, read_idempotency_key(request)
    )


@router.get("/v1/answers/{answer_id}", response_model=Answer)
async def get_answer(
    answer_id: str, container: ContainerDep, principal: PrincipalDep
) -> Answer:
    return await not_implemented(container, "ask", principal, answer_id)


@router.post("/v1/answers/{answer_id}/cancel", response_model=Answer)
async def cancel_answer(
    answer_id: str, container: ContainerDep, principal: PrincipalDep
) -> Answer:
    return await not_implemented(container, "ask", principal, answer_id)


@router.get(
    "/v1/answers/{answer_id}/citations/{citation_id}", response_model=CitationDetail
)
async def get_citation(
    answer_id: str, citation_id: str, container: ContainerDep, principal: PrincipalDep
) -> CitationDetail:
    return await not_implemented(container, "ask", principal, answer_id, citation_id)


@router.get(
    "/v1/answers/{answer_id}/events",
    responses={
        200: {
            "description": "Reserved P3 answer SSE; this build returns 501",
            "content": {"text/event-stream": {"schema": {"type": "string"}}},
        }
    },
)
async def answer_events(
    answer_id: str,
    request: Request,
    container: ContainerDep,
    principal: PrincipalDep,
) -> None:
    # Pre-flight check happens before the stream opens; SSE itself is P3.
    del request
    return await not_implemented(container, "ask", principal, answer_id)
