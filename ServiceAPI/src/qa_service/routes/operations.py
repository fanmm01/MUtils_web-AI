"""Job and widget-ticket routes (A1 owner)."""

from __future__ import annotations

from fastapi import APIRouter

from qa_contracts.operations import Job, WidgetTicket

from ..deps import ContainerDep, PrincipalDep
from ..services import not_implemented

router = APIRouter(tags=["operations"])


@router.get("/v1/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str, container: ContainerDep, principal: PrincipalDep) -> Job:
    return await not_implemented(container, "jobs", principal, job_id)


@router.get("/v1/jobs/{job_id}/events")
async def job_events(job_id: str, container: ContainerDep, principal: PrincipalDep) -> None:
    return await not_implemented(container, "jobs", principal, job_id)


@router.post("/v1/jobs/{job_id}/cancel", response_model=Job)
async def cancel_job(job_id: str, container: ContainerDep, principal: PrincipalDep) -> Job:
    return await not_implemented(container, "jobs", principal, job_id)


@router.post("/v1/widget/tickets", response_model=WidgetTicket, status_code=201)
async def issue_ticket(
    container: ContainerDep, principal: PrincipalDep
) -> WidgetTicket:
    return await not_implemented(container, "widget", principal)
