"""Knowledge-base selection: explicit single/multi, auto routing and session default."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, model_validator

from .base import ID, ContractModel, utc_now


class KBTarget(ContractModel):
    """One knowledge base pinned to an optional immutable version."""

    kb_id: ID
    version_id: ID | None = None


class PinnedKBTarget(ContractModel):
    """An authorized KB resolved to its immutable version before retrieval."""

    kb_id: ID
    version_id: ID


class ExplicitSelection(ContractModel):
    mode: Literal["explicit"] = "explicit"
    targets: Annotated[list[KBTarget], Field(min_length=1)]

    @model_validator(mode="after")
    def _unique_kb(self) -> ExplicitSelection:
        kb_ids = [t.kb_id for t in self.targets]
        if len(set(kb_ids)) != len(kb_ids):
            raise ValueError("a knowledge base may appear only once per request")
        return self


class AutoSelection(ContractModel):
    mode: Literal["auto"] = "auto"
    #: ``None`` means "every base the caller may retrieve"; an empty list is invalid.
    candidate_kb_ids: Annotated[list[ID], Field(min_length=1)] | None = None
    max_kbs: int | None = Field(default=None, ge=1, le=20)

    @model_validator(mode="after")
    def _unique_candidates(self) -> AutoSelection:
        if self.candidate_kb_ids is not None and len(set(self.candidate_kb_ids)) != len(
            self.candidate_kb_ids
        ):
            raise ValueError("candidate_kb_ids must be unique")
        return self


#: Strict discriminated union: clients must state the mode; nothing is inferred.
RetrievalSelection = Annotated[
    ExplicitSelection | AutoSelection, Field(discriminator="mode")
]


class KBDescriptor(ContractModel):
    """Routing metadata an authorized caller may see (no counts, no paths)."""

    kb_id: ID
    name: str
    description: str = ""
    domain_tags: list[str] = Field(default_factory=list)
    routing_examples: list[str] = Field(default_factory=list)
    version_id: ID | None = None


class CatalogQuery(ContractModel):
    search: str | None = None
    limit: int = Field(default=50, ge=1, le=200)
    cursor: str | None = None


class RoutingContext(ContractModel):
    """Model-free context allowed to steer routing (authorized user questions only)."""

    user_questions: list[str] = Field(default_factory=list)
    prior_kb_ids: list[ID] = Field(default_factory=list)


class RankedKB(ContractModel):
    kb_id: ID
    score: float
    reason: str = ""


class ProbeBudget(ContractModel):
    max_kbs: int = Field(ge=1, le=50)
    timeout_ms: int = Field(default=1500, ge=1)
    max_chunks_per_kb: int = Field(default=5, ge=1, le=50)


class ProbeResult(ContractModel):
    kb_id: ID
    version_id: ID
    has_evidence: bool
    score: float = 0.0
    failed: bool = False
    diagnostic: str | None = None


class ProfileGroup(ContractModel):
    """Knowledge bases sharing one embedding profile can reuse a query vector."""

    embedding_profile: str
    kb_ids: list[ID] = Field(default_factory=list)


class SelectionPreviewRequest(ContractModel):
    question: str = Field(min_length=1)
    selection: RetrievalSelection
    inference: InferenceSelection | None = None


class PreparedSelection(ContractModel):
    """Authorized candidates pinned to snapshots; produced before any model call."""

    prepared_id: ID
    requested: RetrievalSelection
    candidates: list[KBDescriptor] = Field(default_factory=list)
    ranked: list[RankedKB] = Field(default_factory=list)
    pinned_targets: list[PinnedKBTarget] = Field(default_factory=list)
    prepared_at: AwareDatetime = Field(default_factory=utc_now)


class SelectionStatus(StrEnum):
    RESOLVED = "resolved"
    NO_MATCH = "no_match"
    NEEDS_CLARIFICATION = "needs_clarification"


class SelectionResult(ContractModel):
    status: SelectionStatus
    mode: Literal["explicit", "auto"]
    targets: list[PinnedKBTarget] = Field(default_factory=list)
    reason: str = ""
    policy_version: str = "p2-keyword"

    @model_validator(mode="after")
    def _targets_match_status(self) -> SelectionResult:
        if self.status == SelectionStatus.RESOLVED and not self.targets:
            raise ValueError("resolved selection requires pinned targets")
        if self.status != SelectionStatus.RESOLVED and self.targets:
            raise ValueError("unresolved selection cannot include targets")
        ids = [target.kb_id for target in self.targets]
        if len(ids) != len(set(ids)):
            raise ValueError("selected knowledge bases must be unique")
        return self


class ResolvedScope(ContractModel):
    scope_id: ID
    targets: Annotated[list[PinnedKBTarget], Field(min_length=1)]
    resolved_at: AwareDatetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def _unique_kb(self) -> ResolvedScope:
        kb_ids = [target.kb_id for target in self.targets]
        if len(set(kb_ids)) != len(kb_ids):
            raise ValueError("resolved scope may include a knowledge base only once")
        return self


class EffectiveSelection(ContractModel):
    selection: RetrievalSelection
    source: Literal["request", "session", "default"] = "default"


class HistoryPolicy(StrEnum):
    RESET_ON_SCOPE_CHANGE = "reset_on_scope_change"
    CARRY_USER_QUESTIONS = "carry_user_questions"


class SessionSelection(ContractModel):
    session_id: ID
    selection: RetrievalSelection
    scope_revision: int = Field(ge=0)
    history_policy: HistoryPolicy = HistoryPolicy.RESET_ON_SCOPE_CHANGE


class ScopeChange(ContractModel):
    expected_scope_revision: int = Field(ge=0)


class UpdateSessionSelection(ContractModel):
    selection: RetrievalSelection
    history_policy: HistoryPolicy = HistoryPolicy.RESET_ON_SCOPE_CHANGE
    expected_scope_revision: int = Field(ge=0)


# Imported late to avoid a cycle between selection and model contracts.
from .models import InferenceSelection  # noqa: E402

SelectionPreviewRequest.model_rebuild()
