"""Principals, jobs, feedback/issues, capabilities and the SSE event union."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, TypeAdapter, model_validator

from .base import HTTP_SCHEMA_VERSION, ID, ContractModel, utc_now


class Principal(ContractModel):
    principal_id: ID
    display_name: str = ""
    is_admin: bool = False


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
    worker_id: ID | None = None
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
    schema_version: int = HTTP_SCHEMA_VERSION
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
    schema_version: Literal[1] = 1
    job_id: ID
    seq: int = Field(ge=1)
    timestamp: AwareDatetime = Field(default_factory=utc_now)
    event: JobEventType
    progress: float | None = Field(default=None, ge=0.0, le=1.0)
    bytes_downloaded: int | None = Field(default=None, ge=0)
    total_bytes: int | None = Field(default=None, ge=0)
    phase: str | None = None
    diagnostic: str | None = None


class JobEventV2(ContractModel):
    """New install/recovery states never overload the persisted v1 event enum."""

    schema_version: Literal[2] = 2
    job_id: ID
    seq: int = Field(ge=1)
    timestamp: AwareDatetime = Field(default_factory=utc_now)
    event: Literal[
        "job.accepted", "job.progress", "job.cancel_requested", "job.outcome_unknown",
        "job.completed", "job.failed", "job.cancelled",
    ]
    progress: float | None = Field(default=None, ge=0.0, le=1.0)
    bytes_downloaded: int | None = Field(default=None, ge=0)
    total_bytes: int | None = Field(default=None, ge=0)
    phase: str | None = None
    diagnostic: str | None = None

    @model_validator(mode="after")
    def _uncertain_outcomes_are_explicit(self) -> JobEventV2:
        if self.event == "job.outcome_unknown" and not self.diagnostic:
            raise ValueError("unknown outcome requires a non-sensitive diagnostic")
        return self


JobEventWire = Annotated[JobEvent | JobEventV2, Field(discriminator="schema_version")]


def parse_job_event(value: Mapping[str, object]) -> JobEvent | JobEventV2:
    """Read persisted v1 without rewriting and new P3 events as v2."""
    version = value.get("schema_version")
    if type(version) is not int or version not in (1, 2):
        raise ValueError(f"unsupported job event schema_version: {version!r}")
    return TypeAdapter(JobEventWire).validate_python(value)


def validate_job_event_sequence_v2(
    events: Iterable[JobEventV2], *, require_terminal: bool = False
) -> None:
    """Replay never treats a pending cancel or unknown transfer as completed."""
    owner: str | None = None
    last_seq = 0
    terminal = False
    seen_cancel = False
    seen_unknown = False
    for event in events:
        if event.schema_version != 2 or event.seq != last_seq + 1 or terminal:
            raise ValueError("non-contiguous sequence, wrong version or event after terminal")
        if owner is None:
            if event.event != "job.accepted":
                raise ValueError("the first event must accept the job")
            owner = event.job_id
        elif event.job_id != owner or event.event == "job.accepted":
            raise ValueError("job ID must stay fixed and acceptance cannot repeat")
        if event.event == "job.cancel_requested":
            if seen_cancel:
                raise ValueError("cancellation may be requested only once")
            seen_cancel = True
        if event.event == "job.outcome_unknown":
            if seen_unknown:
                raise ValueError("unknown transfer outcome may be recorded only once")
            seen_unknown = True
        # A reconciled transfer may complete or fail; a request to cancel may
        # only become cancelled after confirmation, never merely on request.
        if event.event in {"job.completed", "job.failed", "job.cancelled"}:
            terminal = True
        last_seq = event.seq
    if require_terminal and not terminal:
        raise ValueError("the replay has no verified terminal outcome")


from .answers import AnswerEvent, AnswerEventV2  # noqa: E402
from .models import AccessScope as AccessScope  # noqa: E402
from .models import InferenceSelection  # noqa: E402
from .selection import RetrievalSelection  # noqa: E402

RetestRequest.model_rebuild()

#: Answer events carry ``answer_id``; job events carry ``job_id`` and never fake one.
#: Both DTOs forbid extra fields, so a payload validates as exactly one branch.
SSEEvent = AnswerEvent | AnswerEventV2 | JobEvent | JobEventV2


