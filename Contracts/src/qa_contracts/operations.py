"""Principals, jobs, feedback/issues, capabilities and the SSE event union."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, Field

from .base import ID, ContractModel, utc_now
from .models import InferencePolicy


class Principal(ContractModel):
    principal_id: ID
    display_name: str = ""
    is_admin: bool = False


class AccessScope(ContractModel):
    """Authorization facts the domain uses; never derived from client input."""

    principal_id: ID
    kb_ids: list[ID] = Field(default_factory=list)
    can_manage_kb: bool = False
    can_manage_models: bool = False
    allowed_policies: list[InferencePolicy] = Field(default_factory=list)
    allowed_profile_ids: list[ID] = Field(default_factory=list)


class JobKind(StrEnum):
    IMPORT = "import"
    MODEL_INSTALL = "model_install"
    MODEL_VERIFY = "model_verify"


class JobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    CANCEL_REQUESTED = "cancel_requested"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    OUTCOME_UNKNOWN = "outcome_unknown"


class JobFileDiagnostic(ContractModel):
    relative_path: str
    status: Literal["ok", "skipped", "failed"]
    message: str = ""


class Job(ContractModel):
    job_id: ID
    kind: JobKind
    state: JobState = JobState.QUEUED
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    revision: int = Field(ge=0)
    idempotency_key: str | None = None
    lease_until: AwareDatetime | None = None
    result_version_id: ID | None = None
    diagnostics: list[JobFileDiagnostic] = Field(default_factory=list)
    error_code: str | None = None
    created_at: AwareDatetime = Field(default_factory=utc_now)


class JobCommand(ContractModel):
    kind: JobKind
    payload: dict[str, object] = Field(default_factory=dict)
    idempotency_key: str | None = None


class FeedbackInput(ContractModel):
    rating: Literal["like", "dislike"]
    comment: str = ""


class Feedback(ContractModel):
    feedback_id: ID
    answer_id: ID
    principal_id: ID
    rating: Literal["like", "dislike"]
    comment: str = ""
    created_at: AwareDatetime = Field(default_factory=utc_now)


class IssueStatus(StrEnum):
    OPEN = "open"
    LINKED = "linked"
    RESOLVED = "resolved"


class Issue(ContractModel):
    issue_id: ID
    answer_id: ID
    question: str
    status: IssueStatus = IssueStatus.OPEN
    linked_version_id: ID | None = None
    linked_revision_id: ID | None = None
    revision: int = Field(ge=0)
    created_at: AwareDatetime = Field(default_factory=utc_now)


class IssueResolution(ContractModel):
    status: Literal["resolved"] = "resolved"
    note: str = ""


class IssueQuery(ContractModel):
    status: IssueStatus | None = None
    limit: int = Field(default=50, ge=1, le=200)
    cursor: str | None = None


class RetestRequest(ContractModel):
    selection: RetrievalSelection | None = None
    inference: InferenceSelection | None = None


class WidgetTicket(ContractModel):
    ticket: str
    expires_at: AwareDatetime
    kb_ids: list[ID] = Field(default_factory=list)
    session_id: ID | None = None
    profile_ids: list[ID] = Field(default_factory=list)


class Capabilities(ContractModel):
    mode: Literal["scaffold", "operational"] = "scaffold"
    schema_version: int = 1
    implemented: list[str] = Field(default_factory=list)
    unimplemented: list[str] = Field(default_factory=list)
    selection_limits: dict[str, int] = Field(default_factory=dict)


class JobEventType(StrEnum):
    JOB_ACCEPTED = "job.accepted"
    JOB_PROGRESS = "job.progress"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_CANCELLED = "job.cancelled"


class JobEvent(ContractModel):
    schema_version: int = 1
    job_id: ID
    seq: int = Field(ge=1)
    timestamp: AwareDatetime = Field(default_factory=utc_now)
    event: JobEventType
    progress: float | None = Field(default=None, ge=0.0, le=1.0)
    bytes_downloaded: int | None = Field(default=None, ge=0)
    total_bytes: int | None = Field(default=None, ge=0)
    phase: str | None = None
    diagnostic: str | None = None


from .answers import AnswerEvent  # noqa: E402
from .models import InferenceSelection  # noqa: E402
from .selection import RetrievalSelection  # noqa: E402

RetestRequest.model_rebuild()

#: Answer events carry ``answer_id``; job events carry ``job_id`` and never fake one.
#: Both DTOs forbid extra fields, so a payload validates as exactly one branch.
SSEEvent = AnswerEvent | JobEvent


