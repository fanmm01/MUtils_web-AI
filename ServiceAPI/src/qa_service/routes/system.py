"""Health, readiness and capability advertisement."""

from __future__ import annotations

from fastapi import APIRouter

from qa_contracts.base import SCHEMA_VERSION, ContractModel

from ..deps import ContainerDep

router = APIRouter(tags=["system"])


class Health(ContractModel):
    status: str
    mode: str
    schema_version: int = SCHEMA_VERSION


class Readiness(ContractModel):
    ready: bool
    reason: str
    mode: str


class CapabilitiesBody(ContractModel):
    mode: str
    schema_version: int = SCHEMA_VERSION
    implemented: list[str]
    unimplemented: list[str]
    selection_limits: dict[str, int]


@router.get("/healthz", response_model=Health)
async def health(container: ContainerDep) -> Health:
    return Health(status="ok", mode=container.mode)


@router.get("/readyz", response_model=Readiness, status_code=503)
async def readiness(container: ContainerDep) -> Readiness:
    # The scaffold has no database, no worker and no provider: never ready.
    return Readiness(
        ready=False,
        reason="scaffold build has no persistence, worker or model provider",
        mode=container.mode,
    )


@router.get("/v1/capabilities", response_model=CapabilitiesBody)
async def capabilities(container: ContainerDep) -> CapabilitiesBody:
    limits = container.settings.selection
    return CapabilitiesBody(
        mode=container.mode,
        implemented=["health", "readiness", "capabilities"],
        unimplemented=list(container.scaffold_features),
        selection_limits={
            "max_candidate_kbs": limits.max_candidate_kbs,
            "max_selected_kbs": limits.max_selected_kbs,
            "per_kb_candidate_budget": limits.per_kb_candidate_budget,
            "probe_concurrency": limits.probe_concurrency,
            "probe_timeout_ms": limits.probe_timeout_ms,
        },
    )
