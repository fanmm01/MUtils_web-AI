"""Validation for persisted answer event sequences; this module emits no events."""

from __future__ import annotations

from collections.abc import Iterable

from qa_contracts.answers import ANSWER_EVENT_TYPES, AnswerEvent
from qa_contracts.base import SCHEMA_VERSION


class EventSequenceError(ValueError):
    """An answer event stream violates the frozen sequence contract."""


class AnswerEventSequenceValidator:
    """Validate ordering and identity consistency for a replayed event stream."""

    _TERMINAL_EVENTS = {
        "answer.completed",
        "answer.refused",
        "answer.failed",
        "answer.cancelled",
    }

    def __init__(self) -> None:
        self._last_seq = 0
        self._answer_id: str | None = None
        self._session_id: str | None = None
        self._scope_revision: int | None = None
        self._inference_revision: int | None = None
        self._binding_id: str | None = None
        self._scope_id: str | None = None
        self._seen: set[str] = set()
        self._ready_citations: set[str] = set()
        self._terminal = False

    @property
    def terminal(self) -> bool:
        return self._terminal

    def consume(self, event: AnswerEvent) -> None:
        """Accept one event or raise without changing state on invalid input."""
        candidate = self._copy()
        candidate._consume(event)
        self.__dict__.update(candidate.__dict__)

    def validate(self, events: Iterable[AnswerEvent]) -> None:
        """Validate an iterable incrementally, retaining the accepted cursor."""
        for event in events:
            self.consume(event)

    def _copy(self) -> AnswerEventSequenceValidator:
        candidate = AnswerEventSequenceValidator()
        candidate._last_seq = self._last_seq
        candidate._answer_id = self._answer_id
        candidate._session_id = self._session_id
        candidate._scope_revision = self._scope_revision
        candidate._inference_revision = self._inference_revision
        candidate._binding_id = self._binding_id
        candidate._scope_id = self._scope_id
        candidate._seen = self._seen.copy()
        candidate._ready_citations = self._ready_citations.copy()
        candidate._terminal = self._terminal
        return candidate

    def _consume(self, event: AnswerEvent) -> None:
        if event.schema_version != SCHEMA_VERSION:
            raise EventSequenceError(
                f"unsupported event schema_version: {event.schema_version}"
            )
        if event.event not in ANSWER_EVENT_TYPES:
            raise EventSequenceError(f"unknown event type: {event.event}")
        if self._terminal:
            raise EventSequenceError("an event cannot follow a terminal event")
        if event.seq != self._last_seq + 1:
            raise EventSequenceError(
                f"expected seq {self._last_seq + 1}, received {event.seq}"
            )

        if self._answer_id is None:
            if event.event != "answer.accepted":
                raise EventSequenceError("the first event must be answer.accepted")
            self._answer_id = event.answer_id
            self._session_id = event.session_id
            self._scope_revision = event.scope_revision
            self._inference_revision = event.inference_revision
        elif event.event == "answer.accepted":
            raise EventSequenceError("answer.accepted may appear only once")

        self._check_identity(event)
        self._check_order_and_payload(event)
        self._last_seq = event.seq
        self._seen.add(event.event)
        if event.event in self._TERMINAL_EVENTS:
            self._terminal = True

    def _check_identity(self, event: AnswerEvent) -> None:
        if event.answer_id != self._answer_id or event.session_id != self._session_id:
            raise EventSequenceError("answer_id and session_id must remain constant")
        if (
            event.scope_revision != self._scope_revision
            or event.inference_revision != self._inference_revision
        ):
            raise EventSequenceError("selection and inference revisions must remain constant")

        if "inference.bound" not in self._seen:
            if event.event == "inference.bound":
                if event.binding_id is None:
                    raise EventSequenceError("inference.bound requires binding_id")
            elif event.binding_id is not None:
                raise EventSequenceError("binding_id must be null before inference.bound")
        elif event.binding_id != self._binding_id:
            raise EventSequenceError("binding_id must remain constant after binding")

        if "selection.resolved" not in self._seen:
            if event.event == "selection.resolved":
                if event.data.get("status") == "resolved" and event.scope_id is None:
                    raise EventSequenceError("resolved selection requires scope_id")
                if event.data.get("status") != "resolved" and event.scope_id is not None:
                    raise EventSequenceError("unresolved selection cannot have scope_id")
            elif event.scope_id is not None:
                raise EventSequenceError("scope_id must be null before selection.resolved")
        elif event.scope_id != self._scope_id:
            raise EventSequenceError("scope_id must remain constant after selection")

    def _check_order_and_payload(self, event: AnswerEvent) -> None:
        name = event.event
        data = event.data

        if name == "answer.accepted":
            if self._seen:
                raise EventSequenceError("answer.accepted must be the first event")
            if event.binding_id is not None or event.scope_id is not None:
                raise EventSequenceError("accepted event cannot bind inference or scope")
        elif name == "inference.bound":
            self._require("answer.accepted")
            if "inference.bound" in self._seen:
                raise EventSequenceError("inference.bound may appear only once")
            if event.binding_id is None:
                raise EventSequenceError("inference.bound requires binding_id")
            self._binding_id = event.binding_id
        elif name == "selection.resolved":
            self._require("inference.bound")
            if "selection.resolved" in self._seen:
                raise EventSequenceError("selection.resolved may appear only once")
            status = data.get("status")
            if status not in {"resolved", "no_match", "needs_clarification"}:
                raise EventSequenceError("selection.resolved requires a valid status")
            if status == "resolved" and event.scope_id is None:
                raise EventSequenceError("resolved selection requires scope_id")
            if status != "resolved" and event.scope_id is not None:
                raise EventSequenceError("unresolved selection cannot have scope_id")
            self._scope_id = event.scope_id
        elif name == "retrieval.completed":
            self._require("selection.resolved")
            if data.get("status", "completed") != "completed":
                raise EventSequenceError("retrieval.completed requires completed status")
            if self._scope_id is None:
                raise EventSequenceError("retrieval requires a resolved scope")
        elif name == "citation.ready":
            self._require("retrieval.completed")
            citation_id = data.get("citation_id")
            if not isinstance(citation_id, str) or not citation_id:
                raise EventSequenceError("citation.ready requires citation_id")
            if citation_id in self._ready_citations:
                raise EventSequenceError("citation.ready cannot repeat a citation_id")
            self._ready_citations.add(citation_id)
        elif name == "answer.delta":
            self._require("retrieval.completed")
            sentence_id = data.get("sentence_id")
            text = data.get("text")
            citation_ids = data.get("citation_ids", [])
            if not isinstance(sentence_id, str) or not sentence_id:
                raise EventSequenceError("answer.delta requires sentence_id")
            if not isinstance(text, str) or not text:
                raise EventSequenceError("answer.delta requires non-empty verified text")
            if not isinstance(citation_ids, list) or any(
                not isinstance(citation_id, str) or citation_id not in self._ready_citations
                for citation_id in citation_ids
            ):
                raise EventSequenceError("answer.delta may reference only ready citations")
        elif name == "answer.completed":
            self._require("retrieval.completed")
        elif name == "answer.refused":
            self._require("inference.bound")
            if "selection.resolved" not in self._seen:
                raise EventSequenceError("answer.refused requires a selection decision")
            if self._scope_id is None and data.get("reason") not in {
                "no_match",
                "needs_clarification",
            }:
                raise EventSequenceError("unresolved selection refusal requires a routing reason")
            if self._scope_id is not None and "retrieval.completed" not in self._seen:
                raise EventSequenceError("resolved-scope refusal requires retrieval")
        elif name in {"answer.failed", "answer.cancelled"}:
            self._require("answer.accepted")

    def _require(self, event_name: str) -> None:
        if event_name not in self._seen:
            raise EventSequenceError(f"{event_name} must precede the current event")
