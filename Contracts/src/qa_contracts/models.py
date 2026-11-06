"""Model runtimes, inference profiles, install lifecycle and call accounting."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, Field

from .base import ID, ContractModel, utc_now


class RuntimeKind(StrEnum):
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    LLAMA_CPP = "llama_cpp"


class ModelRole(StrEnum):
    GENERATOR = "generator"
    REWRITER = "rewriter"
    SUPPORT_CHECKER = "support_checker"
    RERANKER = "reranker"
    EMBEDDER = "embedder"
    TOKEN_COUNTER = "token_counter"


class InferencePolicy(StrEnum):
    LOCAL_ONLY = "local_only"
    CONFIGURED = "configured"


class Presence(StrEnum):
    """Four independent facts; ``unknown`` is a first-class answer."""

    PRESENT = "present"
    ABSENT = "absent"
    UNKNOWN = "unknown"


class RuntimeTarget(ContractModel):
    """A server-side allow-listed runtime. Clients reference ``target_id`` only."""

    target_id: ID
    kind: RuntimeKind
    display_name: str = ""
    configured: bool = True


class RuntimeEvidence(ContractModel):
    kind: str
    detail: str


class RuntimeStatus(ContractModel):
    target_id: ID
    kind: RuntimeKind
    installed: Presence = Presence.UNKNOWN
    running: Presence = Presence.UNKNOWN
    version: str | None = None
    observed_at: AwareDatetime = Field(default_factory=utc_now)
    evidence: list[RuntimeEvidence] = Field(default_factory=list)
    diagnostic: str | None = None


class RuntimeCapability(ContractModel):
    kind: RuntimeKind
    verified_versions: list[str] = Field(default_factory=list)
    supports_list: Presence = Presence.UNKNOWN
    supports_stream: Presence = Presence.UNKNOWN
    supports_embed: Presence = Presence.UNKNOWN
    supports_install: Presence = Presence.UNKNOWN
    supports_cancel: Presence = Presence.UNKNOWN
    supports_resume: Presence = Presence.UNKNOWN


class ModelCapabilities(ContractModel):
    mode: Literal["scaffold", "operational"] = "scaffold"
    runtimes: list[RuntimeCapability] = Field(default_factory=list)
    install_requires_confirmation: bool = True


class DiscoveryRequest(ContractModel):
    """Only allow-listed runtime IDs; no URL, path, credential or proxy fields."""

    target_ids: list[ID] = Field(default_factory=list)


class DiscoveryReport(ContractModel):
    report_id: ID
    host_id: str
    observed_at: AwareDatetime = Field(default_factory=utc_now)
    runtimes: list[RuntimeStatus] = Field(default_factory=list)


class ModelQuery(ContractModel):
    runtime_target_id: ID | None = None
    role: ModelRole | None = None
    limit: int = Field(default=50, ge=1, le=200)
    cursor: str | None = None


class ModelRef(ContractModel):
    model_id: ID
    runtime_target_id: ID
    exact_tag: str
    family: str | None = None
    parameters: str | None = None
    quantization: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    installed: Presence = Presence.UNKNOWN
    downloaded: Presence = Presence.UNKNOWN
    loaded: Presence = Presence.UNKNOWN
    verified_roles: list[ModelRole] = Field(default_factory=list)
    identity_status: Literal["resolved", "unresolved"] = "unresolved"
    digest: str | None = None


class ModelIdentity(ContractModel):
    model_id: ID
    exact_tag: str
    digest: str | None = None
    identity_status: Literal["resolved", "unresolved"] = "unresolved"


class EmbeddingProfile(ContractModel):
    """Fingerprint pinned into a snapshot; a query must reuse the exact profile."""

    profile_key: str = Field(min_length=1)
    model_id: ID
    digest: str | None = None
    dimension: int = Field(ge=1)
    normalized: bool = True
    preprocessing: str = "none"
    truncation_tokens: int | None = Field(default=None, ge=1)


class InferenceProfile(ContractModel):
    """Immutable profile revision; editing appends a new revision."""

    profile_id: ID
    revision: ID
    roles: dict[ModelRole, ModelIdentity] = Field(default_factory=dict)
    rewriter_enabled: bool = False
    policy_default: InferencePolicy = InferencePolicy.LOCAL_ONLY
    created_at: AwareDatetime = Field(default_factory=utc_now)


class ProfileSummary(ContractModel):
    profile_id: ID
    revision: ID
    policy_default: InferencePolicy
    role_names: list[ModelRole] = Field(default_factory=list)


class PutInferenceProfile(ContractModel):
    profile_id: ID | None = None
    roles: dict[ModelRole, ModelIdentity] = Field(default_factory=dict)
    rewriter_enabled: bool = False
    policy_default: InferencePolicy = InferencePolicy.LOCAL_ONLY
    expected_revision: ID | None = None


class InferenceSelection(ContractModel):
    profile_id: ID | None = None
    policy: InferencePolicy = InferencePolicy.LOCAL_ONLY


class EffectiveInference(ContractModel):
    selection: InferenceSelection
    profile_revision: ID | None = None
    source: Literal["request", "session", "default"] = "default"


class RoleBinding(ContractModel):
    role: ModelRole
    policy: InferencePolicy
    identity: ModelIdentity
    budget_tokens: int | None = Field(default=None, ge=0)


class BindingOwner(ContractModel):
    owner_kind: Literal["answer", "job", "search", "preview"]
    owner_id: ID


class InferenceBinding(ContractModel):
    binding_id: ID
    profile_revision: ID | None = None
    policy: InferencePolicy
    roles: list[RoleBinding] = Field(default_factory=list)
    created_at: AwareDatetime = Field(default_factory=utc_now)


class SessionInference(ContractModel):
    session_id: ID
    inference: InferenceSelection
    inference_revision: int = Field(ge=0)


class UpdateSessionInference(ContractModel):
    inference: InferenceSelection
    expected_inference_revision: int = Field(ge=0)


class InstallRequest(ContractModel):
    target_id: ID
    model_ref: str = Field(min_length=1)


class InstallPreview(ContractModel):
    preview_id: ID
    target_id: ID
    model_ref: str
    preview_hash: str
    identity_status: Literal["resolved", "unresolved"] = "unresolved"
    size_bytes: int | None = Field(default=None, ge=0)
    missing_layers: int | None = Field(default=None, ge=0)
    target_cache: str | None = None
    license_url: str | None = None
    unknown_fields: list[str] = Field(default_factory=list)
    created_at: AwareDatetime = Field(default_factory=utc_now)


class InstallConfirmation(ContractModel):
    preview_id: ID
    preview_hash: str
    confirmed: Literal[True]


class InstallPlan(ContractModel):
    preview_id: ID
    target_id: ID
    model_ref: str


class InstallResult(ContractModel):
    job_id: ID
    model_id: ID
    identity: ModelIdentity


class InstallJobStatus(ContractModel):
    job_id: ID
    phase: str
    bytes_downloaded: int | None = Field(default=None, ge=0)
    total_bytes: int | None = Field(default=None, ge=0)
    diagnostic: str | None = None


class TransferHandle(ContractModel):
    handle_id: ID
    target_id: ID
    model_ref: str


class TransferState(ContractModel):
    handle_id: ID
    phase: str
    bytes_downloaded: int | None = Field(default=None, ge=0)
    total_bytes: int | None = Field(default=None, ge=0)
    outcome_unknown: bool = False


class CancelResult(ContractModel):
    state: Literal["cancel_requested", "cancelled", "outcome_unknown"]


class VerifyModelRequest(ContractModel):
    roles: list[ModelRole] = Field(min_length=1)


class ModelVerification(ContractModel):
    model_id: ID
    target_id: ID
    runtime_version: str | None = None
    verified_roles: list[ModelRole] = Field(default_factory=list)
    failed_roles: list[ModelRole] = Field(default_factory=list)
    verified_at: AwareDatetime = Field(default_factory=utc_now)


class ModelCall(ContractModel):
    call_id: ID
    owner: BindingOwner
    role: ModelRole
    step: int = Field(ge=0)
    started_at: AwareDatetime = Field(default_factory=utc_now)


class CallResult(ContractModel):
    call_id: ID
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    outcome: Literal["ok", "failed", "unknown"] = "ok"


class UsageSummary(ContractModel):
    owner: BindingOwner
    calls: int = Field(default=0, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
