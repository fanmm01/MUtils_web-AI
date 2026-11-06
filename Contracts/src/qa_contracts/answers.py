"""Search/ask requests, sessions, answers, citations and events."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, Field

from .base import ID, ContractModel, utc_now
from .models import EffectiveInference, InferenceBinding, InferenceSelection
from .selection import (
    EffectiveSelection,
    HistoryPolicy,
    ResolvedScope,
    RetrievalSelection,
    SelectionResult,
)


class AnswerTerminal(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    REFUSED = "refused"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SearchRequest(ContractModel):
    question: str = Field(min_length=1)
    selection: RetrievalSelection | None = None
    inference: InferenceSelection | None = None
    top_k: int = Field(default=10, ge=1, le=100)


class Hit(ContractModel):
    """One retrieved chunk; provenance is always per-knowledge-base."""

    kb_id: ID
    version_id: ID
    chunk_id: ID
    text: str
    score: float
    locator: Locator | None = None


class SearchResult(ContractModel):
    selection_result: SelectionResult
    resolved_scope: ResolvedScope | None = None
    hits: list[Hit] = Field(default_factory=list)
    binding_id: ID | None = None


class CreateSession(ContractModel):
    selection: RetrievalSelection | None = None
    inference: InferenceSelection | None = None


class Turn(ContractModel):
    turn_id: ID
    answer_id: ID
    question: str
    answer_text: str = ""
    terminal: AnswerTerminal = AnswerTerminal.COMPLETED
    created_at: AwareDatetime = Field(default_factory=utc_now)


class Session(ContractModel):
    session_id: ID
    principal_id: ID
    selection: RetrievalSelection
    scope_revision: int = Field(ge=0)
    history_policy: HistoryPolicy = HistoryPolicy.RESET_ON_SCOPE_CHANGE
    inference: InferenceSelection
    inference_revision: int = Field(ge=0)
    created_at: AwareDatetime = Field(default_factory=utc_now)


class AnswerContext(ContractModel):
    session_id: ID | None = None
    turns: list[Turn] = Field(default_factory=list)
    history_policy: HistoryPolicy = HistoryPolicy.RESET_ON_SCOPE_CHANGE


class SubmitAnswer(ContractModel):
    question: str = Field(min_length=1)
    selection: RetrievalSelection | None = None
    inference: InferenceSelection | None = None


class AskRequest(ContractModel):
    question: str = Field(min_length=1)
    session_id: ID | None = None
    selection: RetrievalSelection | None = None
    inference: InferenceSelection | None = None
    wait_seconds: float = Field(default=30.0, ge=0, le=120)


class AnswerHandle(ContractModel):
    answer_id: ID
    session_id: ID
    status: AnswerTerminal = AnswerTerminal.PENDING
    poll_url: str
    events_url: str
    retry_after_ms: int = Field(default=500, ge=0)


class AskResponse(ContractModel):
    """Either a finished answer or a handle with polling instructions."""

    answer: Answer | None = None
    handle: AnswerHandle | None = None


class Citation(ContractModel):
    citation_id: ID
    chunk_id: ID
    kb_id: ID
    version_id: ID
    revision_id: ID
    quote: str
    locator: Locator | None = None
    content_hash: str
    detail_path: str


class CitationDetail(ContractModel):
    citation: Citation
    kb_name: str
    document_title: str


class DraftFragment(ContractModel):
    text: str


class DraftSentence(ContractModel):
    sentence_id: ID
    text: str
    citation_ids: list[ID] = Field(default_factory=list)


class VerifiedSentence(ContractModel):
    sentence_id: ID
    text: str
    citations: list[Citation] = Field(default_factory=list)


class GenerationRequest(ContractModel):
    generation_id: ID
    prompt: str
    max_tokens: int = Field(default=1024, ge=1)
    binding_id: ID


class EvidenceDecision(ContractModel):
    sufficient: bool
    reason: str = ""
    conflicting: bool = False


class Answer(ContractModel):
    answer_id: ID
    session_id: ID
    question: str
    status: AnswerTerminal = AnswerTerminal.PENDING
    text: str = ""
    requested_selection: RetrievalSelection | None = None
    selection_result: SelectionResult | None = None
    resolved_scope: ResolvedScope | None = None
    effective_selection: EffectiveSelection | None = None
    effective_inference: EffectiveInference | None = None
    binding: InferenceBinding | None = None
    used_kb_ids: list[ID] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    error_code: str | None = None
    refusal_reason: str | None = None
    created_at: AwareDatetime = Field(default_factory=utc_now)
    completed_at: AwareDatetime | None = None


#: Ordered terminal states; exactly one may be emitted per answer.
ANSWER_EVENT_TYPES = (
    "answer.accepted",
    "inference.bound",
    "selection.resolved",
    "retrieval.completed",
    "citation.ready",
    "answer.delta",
    "answer.completed",
    "answer.refused",
    "answer.failed",
    "answer.cancelled",
)
AnswerEventType = Literal[
    "answer.accepted",
    "inference.bound",
    "selection.resolved",
    "retrieval.completed",
    "citation.ready",
    "answer.delta",
    "answer.completed",
    "answer.refused",
    "answer.failed",
    "answer.cancelled",
]


class AnswerEvent(ContractModel):
    schema_version: Literal[1] = 1
    answer_id: ID
    session_id: ID
    seq: int = Field(ge=1)
    timestamp: AwareDatetime = Field(default_factory=utc_now)
    event: AnswerEventType
    scope_revision: int | None = Field(default=None, ge=0)
    inference_revision: int | None = Field(default=None, ge=0)
    binding_id: ID | None = None
    scope_id: ID | None = None
    data: dict[str, object] = Field(default_factory=dict)


from .knowledge import Locator  # noqa: E402

Hit.model_rebuild()
Citation.model_rebuild()
CitationDetail.model_rebuild()
SearchResult.model_rebuild()
AskResponse.model_rebuild()
