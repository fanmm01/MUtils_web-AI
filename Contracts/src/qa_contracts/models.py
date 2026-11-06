"""Model runtimes, inference profiles, install lifecycle and call accounting."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from .base import ID, ContractModel, utc_now
from .errors import (
    InferencePolicyViolation,
    ModelCapabilityMissing,
    ModelChanged,
    PermissionDenied,
)


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


class AccessScope(ContractModel):
    """Server-derived permissions; never constructed from request JSON."""

    principal_id: ID
    kb_ids: list[ID] = Field(default_factory=list)
    can_manage_kb: bool = False
    can_manage_models: bool = False
    allowed_policies: list[InferencePolicy] = Field(default_factory=list)
    allowed_profile_ids: list[ID] = Field(default_factory=list)


class ExecutionLocation(StrEnum):
    LOCAL = "local"
    CONFIGURED_REMOTE = "configured_remote"


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
    location: ExecutionLocation = ExecutionLocation.LOCAL


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

    @model_validator(mode="after")
    def _identity_consistent(self) -> ModelRef:
        if self.identity_status == "resolved" and (
            self.digest is None
            or not self.digest.startswith("sha256:")
            or len(self.digest) != len("sha256:") + 64
            or any(char not in "0123456789abcdef" for char in self.digest[7:].lower())
        ):
            raise ValueError("a resolved model reference requires a complete sha256 digest")
        if self.identity_status == "unresolved" and self.digest is not None:
            raise ValueError("an unresolved model reference cannot claim a digest")
        return self


class ModelIdentity(ContractModel):
    """An exact tag is an alias; only a resolved digest pins model bytes.

    An adapter must compare this identity with a fresh runtime observation before
    every call. A mutable tag alone cannot promise reproducible results.
    """

    model_id: ID
    exact_tag: str = Field(min_length=1)
    digest: str | None = None
    identity_status: Literal["resolved", "unresolved"] = "unresolved"
    runtime_target_id: ID | None = None

    @model_validator(mode="after")
    def _resolved_has_digest(self) -> ModelIdentity:
        if self.identity_status == "resolved" and (
            self.digest is None
            or not self.digest.startswith("sha256:")
            or len(self.digest) != len("sha256:") + 64
            or any(char not in "0123456789abcdef" for char in self.digest[7:].lower())
        ):
            raise ValueError("a resolved model identity requires a complete sha256 digest")
        if self.identity_status == "unresolved" and self.digest is not None:
            raise ValueError("an unresolved model identity cannot claim a digest")
        return self

    def assert_unchanged(self, observed: ModelIdentity) -> None:
        """Fail closed on identity drift or an unresolved/ambiguous label."""
        if (
            self.identity_status != "resolved"
            or observed.identity_status != "resolved"
            or not self.digest
            or not observed.digest
            or self.model_id != observed.model_id
            or self.exact_tag != observed.exact_tag
            or self.digest != observed.digest
            or (
                self.runtime_target_id is not None
                and self.runtime_target_id != observed.runtime_target_id
            )
        ):
            raise ModelChanged(self.digest or "unresolved", observed.digest or "unresolved")


class EmbeddingProfile(ContractModel):
    """Full snapshot fingerprint; only a resolved identity is usable for vectors."""

    profile_key: str = Field(min_length=1)
    model_id: ID
    digest: str | None = None
    dimension: int = Field(ge=1)
    normalized: bool = True
    preprocessing: str = Field(default="none", min_length=1)
    truncation_tokens: int | None = Field(default=None, ge=1)
    truncation_policy: Literal["reject", "truncate"] = "reject"
    identity: ModelIdentity | None = None

    @model_validator(mode="after")
    def _consistent_identity(self) -> EmbeddingProfile:
        if self.identity is not None and (
            self.identity.model_id != self.model_id or self.identity.digest != self.digest
        ):
            raise ValueError("embedding identity must match model ID and digest")
        if self.truncation_policy == "truncate" and self.truncation_tokens is None:
            raise ValueError("truncate policy requires an explicit token limit")
        return self

    def fingerprint(self) -> str:
        """Reject legacy tag-only vectors instead of labelling them reproducible."""
        if self.identity is None or self.identity.identity_status != "resolved" or not self.digest:
            raise ValueError("vector profiles require a resolved model identity")
        payload = {
            "runtime_target_id": self.identity.runtime_target_id,
            "model_id": self.model_id,
            "exact_tag": self.identity.exact_tag,
            "digest": self.digest,
            "dimension": self.dimension,
            "normalized": self.normalized,
            "preprocessing": self.preprocessing,
            "truncation_tokens": self.truncation_tokens,
            "truncation_policy": self.truncation_policy,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return sha256(encoded).hexdigest()


class InferenceProfile(ContractModel):
    """Immutable profile revision; editing appends a new revision."""

    profile_id: ID
    revision: ID
    roles: dict[ModelRole, ModelIdentity] = Field(default_factory=dict)
    rewriter_enabled: bool = False
    policy_default: InferencePolicy = InferencePolicy.LOCAL_ONLY
    created_at: AwareDatetime = Field(default_factory=utc_now)

    def require_role(self, role: ModelRole) -> ModelIdentity:
        identity = self.roles.get(role)
        if identity is None:
            raise ModelCapabilityMissing(role.value)
        return identity


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
    location: ExecutionLocation = ExecutionLocation.LOCAL
    runtime_target_id: ID | None = None
    timeout_ms: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _policy_matches_location(self) -> RoleBinding:
        if self.policy == InferencePolicy.LOCAL_ONLY and self.location != ExecutionLocation.LOCAL:
            raise InferencePolicyViolation(self.role.value)
        if self.identity.runtime_target_id is not None and (
            self.runtime_target_id != self.identity.runtime_target_id
        ):
            raise ValueError("role binding runtime must match the exact model identity")
        return self


def authorize_role_binding(
    binding: RoleBinding, targets: list[RuntimeTarget], observed: ModelIdentity
) -> RuntimeTarget:
    """Recheck a call against a server-owned target and current model identity."""
    target = next(
        (
            item for item in targets
            if item.configured and item.target_id == binding.runtime_target_id
        ),
        None,
    )
    if target is None:
        raise ModelCapabilityMissing(binding.role.value)
    if binding.location != target.location or (
        binding.policy == InferencePolicy.LOCAL_ONLY
        and target.location != ExecutionLocation.LOCAL
    ):
        raise InferencePolicyViolation(binding.role.value)
    binding.identity.assert_unchanged(observed)
    return target


class CandidateEmbedder(ContractModel):
    """One candidate snapshot is pinned to its exact embedding role and profile."""

    kb_id: ID
    version_id: ID
    fingerprint: str = Field(min_length=1)
    binding: RoleBinding

    @model_validator(mode="after")
    def _requires_embedder(self) -> CandidateEmbedder:
        if self.binding.role != ModelRole.EMBEDDER:
            raise ValueError("candidate embedding must bind the embedder role")
        return self


class BindingOwner(ContractModel):
    owner_kind: Literal["answer", "job", "search", "preview"]
    owner_id: ID


class InferenceBinding(ContractModel):
    binding_id: ID
    profile_revision: ID | None = None
    policy: InferencePolicy
    roles: list[RoleBinding] = Field(default_factory=list)
    candidate_embedders: list[CandidateEmbedder] = Field(default_factory=list)
    created_at: AwareDatetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def _fixed_roles_and_candidates(self) -> InferenceBinding:
        names = [item.role for item in self.roles]
        if len(names) != len(set(names)):
            raise ValueError("each inference role may be bound only once")
        candidates = [(item.kb_id, item.version_id) for item in self.candidate_embedders]
        if len(candidates) != len(set(candidates)):
            raise ValueError("each candidate snapshot requires exactly one embedding binding")
        for item in [*self.roles, *(candidate.binding for candidate in self.candidate_embedders)]:
            if item.policy != self.policy:
                raise ValueError("binding policy must match every role and candidate")
        return self

    def require_role(self, role: ModelRole) -> RoleBinding:
        for bound in self.roles:
            if bound.role == role:
                return bound
        raise ModelCapabilityMissing(role.value)

    def require_embedder(self, kb_id: ID, version_id: ID) -> CandidateEmbedder:
        for candidate in self.candidate_embedders:
            if candidate.kb_id == kb_id and candidate.version_id == version_id:
                return candidate
        raise ModelCapabilityMissing(ModelRole.EMBEDDER.value)


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

    def authorize(self, targets: list[RuntimeTarget], access: AccessScope) -> RuntimeTarget:
        if not access.can_manage_models:
            raise PermissionDenied("model installation")
        target = next(
            (item for item in targets if item.configured and item.target_id == self.target_id),
            None,
        )
        if target is None:
            raise ModelCapabilityMissing(ModelRole.GENERATOR.value)
        return target


class InstallPreview(ContractModel):
    preview_id: ID
    target_id: ID
    target_location: ExecutionLocation
    model_ref: str
    preview_hash: str
    identity_status: Literal["resolved", "unresolved"] = "unresolved"
    expected_identity: ModelIdentity | None = None
    principal_id: ID
    expires_at: AwareDatetime
    size_bytes: int | None = Field(default=None, ge=0)
    missing_layers: int | None = Field(default=None, ge=0)
    target_cache: str | None = None
    license_url: str | None = None
    unknown_fields: list[str] = Field(default_factory=list)
    created_at: AwareDatetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def _identity_and_expiry(self) -> InstallPreview:
        if self.expires_at <= self.created_at:
            raise ValueError("install preview expiry must be later than creation")
        if self.target_location == ExecutionLocation.LOCAL and self.target_cache is not None and (
            "://" in self.target_cache
            or self.target_cache.startswith(("/", "\\\\"))
            or (
                ":" in self.target_cache
                and ("/" in self.target_cache or "\\\\" in self.target_cache)
            )
        ):
            raise ValueError("target cache must be a server-owned opaque label, not a path or URL")
        if self.expected_identity is not None and (
            self.expected_identity.identity_status != self.identity_status
        ):
            raise ValueError("preview identity status must match observed identity")
        return self

    def assert_confirmable(
        self, principal_id: ID, now: datetime, confirmation: InstallConfirmation | None = None,
        observed_identity: ModelIdentity | None = None,
    ) -> None:
        """Reject stale previews or tag drift; unknown digest is not a verified binding."""
        if self.principal_id != principal_id or now >= self.expires_at:
            raise ValueError("install preview is expired or belongs to another principal")
        if confirmation is not None and (
            confirmation.preview_id != self.preview_id
            or confirmation.preview_hash != self.preview_hash
        ):
            raise ValueError("install confirmation does not match the preview")
        if self.expected_identity is not None:
            if observed_identity is None:
                raise ModelChanged(self.expected_identity.digest or "unresolved", "unobserved")
            self.expected_identity.assert_unchanged(observed_identity)


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

    @model_validator(mode="after")
    def _uncertain_is_not_completed(self) -> TransferState:
        if self.outcome_unknown and self.phase in {"completed", "cancelled"}:
            raise ValueError("unknown transfer cannot claim a confirmed terminal state")
        return self


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
