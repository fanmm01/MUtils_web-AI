"""Search/ask requests, sessions, answers, citations and events."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, TypeAdapter, model_validator

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


class PinnedTurn(Turn):
    """One completed turn pins its own scope and inference, not session defaults."""

    scope_revision: int = Field(ge=0)
    inference_revision: int = Field(ge=0)
    resolved_scope: ResolvedScope
    effective_inference: EffectiveInference
    binding_id: ID | None = None
    segment_id: ID


class HistorySegment(ContractModel):
    """History from one immutable scope; old answers cannot cross segments."""

    segment_id: ID
    resolved_scope: ResolvedScope
    turns: list[PinnedTurn] = Field(default_factory=list)

    @model_validator(mode="after")
    def _consistent_turns(self) -> HistorySegment:
        if any(
            turn.segment_id != self.segment_id
            or turn.resolved_scope != self.resolved_scope
            or turn.terminal != AnswerTerminal.COMPLETED
            for turn in self.turns
        ):
            raise ValueError("history turns must be completed in their immutable segment")
        return self


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
    # P3 consumers use explicit segments; turns remains readable for P1/P2 callers.
    segments: list[HistorySegment] = Field(default_factory=list)
    current_segment_id: ID | None = None

    @model_validator(mode="after")
    def _current_segment_exists(self) -> AnswerContext:
        ids = [segment.segment_id for segment in self.segments]
        if len(set(ids)) != len(ids):
            raise ValueError("history segment IDs must be unique")
        if self.current_segment_id is not None and self.current_segment_id not in ids:
            raise ValueError("the current history segment must exist")
        return self


class PinnedAnswerContext(ContractModel):
    """The only history payload a P3 generation call may receive.

    Old segments remain in Session history for viewing, not in this model input.
    The caller may explicitly copy authorized *user questions* into
    ``carry_user_questions``; it cannot carry old answers or citations.
    """

    session_id: ID
    scope_revision: int = Field(ge=0)
    inference_revision: int = Field(ge=0)
    resolved_scope: ResolvedScope
    current_segment_id: ID
    turns: list[PinnedTurn] = Field(default_factory=list)
    carry_user_questions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _only_current_scope(self) -> PinnedAnswerContext:
        if any(
            turn.segment_id != self.current_segment_id
            or turn.resolved_scope != self.resolved_scope
            or turn.terminal != AnswerTerminal.COMPLETED
            or turn.scope_revision != self.scope_revision
            or turn.inference_revision != self.inference_revision
            for turn in self.turns
        ):
            raise ValueError("generation history may include only completed current-scope turns")
        return self


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


class AnswerAcceptedData(ContractModel):
    """The accepted request fixes revisions before any model is called."""


class InferenceBoundData(ContractModel):
    binding: InferenceBinding


class SelectionResolvedData(ContractModel):
    result: SelectionResult
    resolved_scope: ResolvedScope | None = None

    @model_validator(mode="after")
    def _scope_matches_result(self) -> SelectionResolvedData:
        if self.result.status.value == "resolved":
            if self.resolved_scope is None or self.resolved_scope.targets != self.result.targets:
                raise ValueError("resolved selection requires the same pinned targets")
        elif self.resolved_scope is not None:
            raise ValueError("unresolved selection cannot bind a scope")
        return self


class RetrievalCompletedData(ContractModel):
    hit_count: int = Field(ge=0)


class CitationReadyData(ContractModel):
    citation: Citation


class AnswerDeltaData(ContractModel):
    sentence_id: ID
    text: str = Field(min_length=1)
    citation_ids: list[ID] = Field(min_length=1)


class AnswerCompletedData(ContractModel):
    answer: Answer

    @model_validator(mode="after")
    def _completed(self) -> AnswerCompletedData:
        if self.answer.status != AnswerTerminal.COMPLETED:
            raise ValueError("a completed event must contain a completed final answer")
        return self


class AnswerRefusedData(ContractModel):
    reason: str = Field(min_length=1)


class AnswerFailedData(ContractModel):
    reason: str = Field(min_length=1)
    incomplete: bool = False


class AnswerCancelledData(ContractModel):
    reason: str = Field(min_length=1)
    incomplete: bool = False


class AnswerEventV2(ContractModel):
    """P3 wire basis. Unlike v1, both accepted revisions are mandatory."""

    schema_version: Literal[2] = 2
    answer_id: ID
    session_id: ID
    seq: int = Field(ge=1)
    timestamp: AwareDatetime = Field(default_factory=utc_now)
    scope_revision: int = Field(ge=0)
    inference_revision: int = Field(ge=0)
    # Null before binding/resolution, then fixed for the rest of this answer.
    binding_id: ID | None = Field(...)
    scope_id: ID | None = Field(...)


class AnswerAcceptedV2(AnswerEventV2):
    event: Literal["answer.accepted"] = "answer.accepted"
    data: AnswerAcceptedData

    @model_validator(mode="after")
    def _unbound(self) -> AnswerAcceptedV2:
        if self.binding_id is not None or self.scope_id is not None:
            raise ValueError("an accepted answer has no binding or scope")
        return self


class InferenceBoundV2(AnswerEventV2):
    event: Literal["inference.bound"] = "inference.bound"
    data: InferenceBoundData

    @model_validator(mode="after")
    def _binding_matches(self) -> InferenceBoundV2:
        if self.binding_id != self.data.binding.binding_id or self.scope_id is not None:
            raise ValueError("binding ID must match and scope must remain unbound")
        return self


class SelectionResolvedV2(AnswerEventV2):
    event: Literal["selection.resolved"] = "selection.resolved"
    data: SelectionResolvedData

    @model_validator(mode="after")
    def _scope_matches(self) -> SelectionResolvedV2:
        if self.binding_id is None:
            raise ValueError("selection must follow an inference binding")
        scope = self.data.resolved_scope
        if self.scope_id != (scope.scope_id if scope else None):
            raise ValueError("scope ID must equal the resolved scope, if any")
        return self


class RetrievalCompletedV2(AnswerEventV2):
    event: Literal["retrieval.completed"] = "retrieval.completed"
    data: RetrievalCompletedData


class CitationReadyV2(AnswerEventV2):
    event: Literal["citation.ready"] = "citation.ready"
    data: CitationReadyData


class AnswerDeltaV2(AnswerEventV2):
    event: Literal["answer.delta"] = "answer.delta"
    data: AnswerDeltaData


class AnswerCompletedV2(AnswerEventV2):
    event: Literal["answer.completed"] = "answer.completed"
    data: AnswerCompletedData

    @model_validator(mode="after")
    def _final_identity(self) -> AnswerCompletedV2:
        answer = self.data.answer
        if answer.answer_id != self.answer_id or answer.session_id != self.session_id:
            raise ValueError("final answer identity must equal the event identity")
        if answer.resolved_scope is None or answer.resolved_scope.scope_id != self.scope_id:
            raise ValueError("final answer must use the bound scope")
        if answer.binding is None or answer.binding.binding_id != self.binding_id:
            raise ValueError("final answer must use the bound inference")
        return self


class AnswerRefusedV2(AnswerEventV2):
    event: Literal["answer.refused"] = "answer.refused"
    data: AnswerRefusedData


class AnswerFailedV2(AnswerEventV2):
    event: Literal["answer.failed"] = "answer.failed"
    data: AnswerFailedData


class AnswerCancelledV2(AnswerEventV2):
    event: Literal["answer.cancelled"] = "answer.cancelled"
    data: AnswerCancelledData


AnswerEventV2Wire = Annotated[
    AnswerAcceptedV2 | InferenceBoundV2 | SelectionResolvedV2 | RetrievalCompletedV2
    | CitationReadyV2 | AnswerDeltaV2 | AnswerCompletedV2 | AnswerRefusedV2
    | AnswerFailedV2 | AnswerCancelledV2,
    Field(discriminator="event"),
]


def parse_answer_event(value: Mapping[str, object]) -> AnswerEvent | AnswerEventV2:
    """Read recorded v1 unchanged and validate new events against v2 by event type."""
    version = value.get("schema_version")
    if type(version) is int and version == 1:
        return AnswerEvent.model_validate(value)
    if type(version) is int and version == 2:
        return TypeAdapter(AnswerEventV2Wire).validate_python(value)
    raise ValueError(f"unsupported answer event schema_version: {version!r}")


def validate_answer_event_sequence_v2(
    events: Iterable[AnswerEventV2], *, require_terminal: bool = False
) -> None:
    """Freeze replay order, immutable identities and citation-before-delta semantics."""
    last_seq = 0
    owner: tuple[str, str, int, int] | None = None
    binding_id: str | None = None
    scope_id: str | None = None
    resolved_targets: set[tuple[str, str]] | None = None
    seen: set[str] = set()
    citations: dict[str, Citation] = {}
    delta_text: list[str] = []
    delta_citation_ids: set[str] = set()
    has_delta = False
    selection_status: str | None = None
    terminal = False
    for event in events:
        if event.schema_version != 2 or last_seq + 1 != event.seq or terminal:
            raise ValueError("non-contiguous sequence, wrong version or event after terminal")
        identity = (
            event.answer_id, event.session_id, event.scope_revision, event.inference_revision
        )
        if owner is None:
            if event.event != "answer.accepted":
                raise ValueError("the first event must accept the answer")
            owner = identity
        elif identity != owner or event.event == "answer.accepted":
            raise ValueError("answer identity/revisions must remain fixed")
        name = event.event
        if name == "inference.bound":
            if "answer.accepted" not in seen or binding_id is not None:
                raise ValueError("inference can be bound only once after acceptance")
            binding_id = event.binding_id
        elif binding_id is None and name not in {
            "answer.accepted", "answer.failed", "answer.cancelled"
        }:
            raise ValueError("inference binding must precede the event")
        if name == "selection.resolved":
            if "inference.bound" not in seen or "selection.resolved" in seen:
                raise ValueError("selection may resolve only once after binding")
            scope_id = event.scope_id
            selection_status = event.data.result.status.value
            if event.data.resolved_scope is not None:
                resolved_targets = {
                    (target.kb_id, target.version_id)
                    for target in event.data.resolved_scope.targets
                }
        elif name not in {
            "answer.accepted", "inference.bound", "answer.failed", "answer.cancelled"
        }:
            if "selection.resolved" not in seen:
                raise ValueError("selection must precede the event")
        if name not in {"answer.accepted", "inference.bound"}:
            if event.binding_id != binding_id:
                raise ValueError("binding cannot change or become non-null early")
        if name != "selection.resolved" and event.scope_id != scope_id:
            raise ValueError("scope cannot change or become non-null early")
        if name == "retrieval.completed":
            if scope_id is None or name in seen:
                raise ValueError("retrieval requires a unique resolved scope")
        elif name == "citation.ready":
            if "retrieval.completed" not in seen or event.data.citation.citation_id in citations:
                raise ValueError("citations require retrieval and unique citation IDs")
            citation = event.data.citation
            if (
                event.scope_id is None
                or resolved_targets is None
                or (citation.kb_id, citation.version_id) not in resolved_targets
                or citation.detail_path != (
                    f"/v1/answers/{event.answer_id}/citations/{citation.citation_id}"
                )
            ):
                raise ValueError("ready citation must match this answer's pinned scope")
            citations[citation.citation_id] = citation
        elif name == "answer.delta":
            if "retrieval.completed" not in seen or any(
                citation not in citations for citation in event.data.citation_ids
            ):
                raise ValueError("verified delta may reference only ready citations")
            delta_text.append(event.data.text)
            delta_citation_ids.update(event.data.citation_ids)
            has_delta = True
        elif name == "answer.completed":
            if not has_delta or scope_id is None:
                raise ValueError("completion requires verified delta and resolved scope")
            answer = event.data.answer
            if answer.text != "".join(delta_text):
                raise ValueError("the final JSON answer must match verified stream text")
            if {citation.citation_id for citation in answer.citations} != delta_citation_ids:
                raise ValueError("the final JSON answer must contain referenced citations")
            if any(
                citations.get(ready.citation_id) != ready for ready in answer.citations
            ):
                raise ValueError("final citation details must match previously ready citations")
        elif name == "answer.refused":
            if "selection.resolved" not in seen or has_delta:
                raise ValueError("refusal requires selection and cannot hide partial output")
            if scope_id is None and event.data.reason != selection_status:
                raise ValueError("an unresolved selection must explain its refusal")
            if scope_id is not None and "retrieval.completed" not in seen:
                raise ValueError("resolved-scope refusal requires completed retrieval")
        elif name in {"answer.failed", "answer.cancelled"}:
            if has_delta and not event.data.incomplete:
                raise ValueError("partial output failure/cancellation must be marked incomplete")
        if name in {"answer.completed", "answer.refused", "answer.failed", "answer.cancelled"}:
            terminal = True
        seen.add(name)
        last_seq = event.seq
    if require_terminal and not terminal:
        raise ValueError("a complete answer replay requires one terminal event")


from .knowledge import Locator  # noqa: E402

Hit.model_rebuild()
Citation.model_rebuild()
CitationDetail.model_rebuild()
SearchResult.model_rebuild()
AskResponse.model_rebuild()
