"""Model discovery, profile, install and session-inference routes.

These are A2 semantics with A1 route wiring. Every effective business request
returns 501; discovery must never accept a client-supplied URL or path, so the
request DTO has no such field and ``extra="forbid"`` rejects the attempt.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from qa_contracts.base import Page
from qa_contracts.models import (
    DiscoveryReport,
    DiscoveryRequest,
    InferenceProfile,
    InstallConfirmation,
    InstallPreview,
    InstallRequest,
    ModelCapabilities,
    ModelQuery,
    ModelRef,
    Presence,
    ProfileSummary,
    PutInferenceProfile,
    RuntimeCapability,
    RuntimeStatus,
    SessionInference,
    UpdateSessionInference,
    VerifyModelRequest,
)
from qa_contracts.operations import Job

from ..deps import ContainerDep, PrincipalDep
from ..services import not_implemented

router = APIRouter(tags=["models"])


@router.get("/v1/models/capabilities", response_model=ModelCapabilities)
async def model_capabilities(
    container: ContainerDep, principal: PrincipalDep
) -> ModelCapabilities:
    del principal
    # Static scaffold capabilities only; no probing, no model listing.
    return ModelCapabilities(
        mode="scaffold",
        runtimes=[
            RuntimeCapability(
                kind=target.kind,
                verified_versions=[],
                supports_list=Presence.UNKNOWN,
                supports_stream=Presence.UNKNOWN,
                supports_embed=Presence.UNKNOWN,
                supports_install=Presence.UNKNOWN,
                supports_cancel=Presence.UNKNOWN,
                supports_resume=Presence.UNKNOWN,
            )
            for target in container.settings.runtime_targets
        ],
        install_requires_confirmation=True,
    )


@router.post("/v1/models/discovery", response_model=DiscoveryReport, status_code=202)
async def discover_runtimes(
    body: DiscoveryRequest, container: ContainerDep, principal: PrincipalDep
) -> DiscoveryReport:
    return await not_implemented(container, "models", principal, body)


@router.get("/v1/models/runtimes", response_model=list[RuntimeStatus])
async def list_runtimes(
    container: ContainerDep, principal: PrincipalDep
) -> list[RuntimeStatus]:
    return await not_implemented(container, "models", principal)


@router.get("/v1/models", response_model=Page[ModelRef])
async def list_models(
    query: Annotated[ModelQuery, Query()],
    container: ContainerDep,
    principal: PrincipalDep,
) -> Page[ModelRef]:
    return await not_implemented(container, "models", principal, query)


@router.get("/v1/models/{model_id}", response_model=ModelRef)
async def get_model(
    model_id: str, container: ContainerDep, principal: PrincipalDep
) -> ModelRef:
    return await not_implemented(container, "models", principal, model_id)


@router.get("/v1/inference-profiles", response_model=Page[ProfileSummary])
async def list_profiles(
    container: ContainerDep, principal: PrincipalDep
) -> Page[ProfileSummary]:
    return await not_implemented(container, "models", principal)


@router.post("/v1/inference-profiles", response_model=InferenceProfile, status_code=201)
async def create_profile(
    body: PutInferenceProfile, container: ContainerDep, principal: PrincipalDep
) -> InferenceProfile:
    return await not_implemented(container, "models", principal, body)


@router.get("/v1/inference-profiles/{profile_id}", response_model=InferenceProfile)
async def get_profile(
    profile_id: str,
    container: ContainerDep,
    principal: PrincipalDep,
    revision: str | None = None,
) -> InferenceProfile:
    return await not_implemented(container, "models", principal, profile_id, revision)


@router.put("/v1/inference-profiles/{profile_id}", response_model=InferenceProfile)
async def update_profile(
    profile_id: str, body: PutInferenceProfile, container: ContainerDep,
    principal: PrincipalDep,
) -> InferenceProfile:
    return await not_implemented(container, "models", principal, profile_id, body)


@router.post("/v1/inference-profiles/{profile_id}/disable", response_model=InferenceProfile)
async def disable_profile(
    profile_id: str,
    body: PutInferenceProfile,
    container: ContainerDep,
    principal: PrincipalDep,
) -> InferenceProfile:
    return await not_implemented(container, "models", principal, profile_id, body)


@router.get("/v1/sessions/{session_id}/inference", response_model=SessionInference)
async def get_session_inference(
    session_id: str, container: ContainerDep, principal: PrincipalDep
) -> SessionInference:
    return await not_implemented(container, "models", principal, session_id)


@router.patch("/v1/sessions/{session_id}/inference", response_model=SessionInference)
async def update_session_inference(
    session_id: str,
    body: UpdateSessionInference,
    container: ContainerDep,
    principal: PrincipalDep,
) -> SessionInference:
    return await not_implemented(container, "models", principal, session_id, body)


@router.post("/v1/model-installs/preview", response_model=InstallPreview, status_code=202)
async def preview_install(
    body: InstallRequest, container: ContainerDep, principal: PrincipalDep
) -> InstallPreview:
    return await not_implemented(container, "models", principal, body)


@router.post("/v1/model-installs", response_model=Job, status_code=202)
async def confirm_install(
    body: InstallConfirmation, container: ContainerDep, principal: PrincipalDep
) -> Job:
    # There is no install path in the scaffold, so confirmation cannot succeed
    # even with a well-formed preview reference.
    return await not_implemented(container, "models", principal, body)


@router.post("/v1/models/{model_id}/verifications", response_model=Job, status_code=202)
async def verify_model(
    model_id: str, body: VerifyModelRequest, container: ContainerDep, principal: PrincipalDep
) -> Job:
    return await not_implemented(container, "models", principal, model_id, body)
