from datetime import UTC, datetime

import pytest

from qa_assistant.events import AnswerEventSequenceValidator, EventSequenceError
from qa_contracts.answers import AnswerEvent


def event(seq: int, name: str, **kwargs: object) -> AnswerEvent:
    values: dict[str, object] = {
        "answer_id": "answer-1",
        "session_id": "session-1",
        "seq": seq,
        "timestamp": datetime.now(UTC),
        "event": name,
        "scope_revision": 2,
        "inference_revision": 3,
        "data": {},
    }
    values.update(kwargs)
    return AnswerEvent(**values)


def successful_events() -> list[AnswerEvent]:
    return [
        event(1, "answer.accepted"),
        event(2, "inference.bound", binding_id="binding-1"),
        event(
            3,
            "selection.resolved",
            binding_id="binding-1",
            scope_id="scope-1",
            data={"status": "resolved", "targets": []},
        ),
        event(
            4,
            "retrieval.completed",
            binding_id="binding-1",
            scope_id="scope-1",
            data={"status": "completed"},
        ),
        event(
            5,
            "citation.ready",
            binding_id="binding-1",
            scope_id="scope-1",
            data={"citation_id": "citation-1"},
        ),
        event(
            6,
            "answer.delta",
            binding_id="binding-1",
            scope_id="scope-1",
            data={
                "sentence_id": "sentence-1",
                "text": "A verified statement.",
                "citation_ids": ["citation-1"],
            },
        ),
        event(
            7,
            "answer.completed",
            binding_id="binding-1",
            scope_id="scope-1",
        ),
    ]


def test_valid_answer_sequence_reaches_one_terminal_state() -> None:
    validator = AnswerEventSequenceValidator()
    validator.validate(successful_events())

    assert validator.terminal


def test_replay_validation_requires_the_original_prefix() -> None:
    validator = AnswerEventSequenceValidator()

    with pytest.raises(EventSequenceError, match="expected seq 1"):
        validator.consume(successful_events()[3])


def test_sequence_gap_is_rejected_without_advancing_cursor() -> None:
    validator = AnswerEventSequenceValidator()
    validator.consume(event(1, "answer.accepted"))

    with pytest.raises(EventSequenceError, match="expected seq 2"):
        validator.consume(event(3, "inference.bound", binding_id="binding-1"))

    validator.consume(event(2, "inference.bound", binding_id="binding-1"))


def test_delta_cannot_reference_citation_before_ready() -> None:
    validator = AnswerEventSequenceValidator()
    validator.validate(successful_events()[:4])
    delta = event(
        5,
        "answer.delta",
        binding_id="binding-1",
        scope_id="scope-1",
        data={"sentence_id": "s1", "text": "text", "citation_ids": ["c1"]},
    )

    with pytest.raises(EventSequenceError, match="ready citations"):
        validator.consume(delta)


def test_binding_identity_cannot_change_after_bind() -> None:
    validator = AnswerEventSequenceValidator()
    validator.validate(successful_events()[:2])

    with pytest.raises(EventSequenceError, match="binding_id must remain constant"):
        validator.consume(
            event(3, "selection.resolved", binding_id="binding-2", data={"status": "no_match"})
        )


def test_event_after_terminal_is_rejected() -> None:
    validator = AnswerEventSequenceValidator()
    validator.validate(successful_events())

    with pytest.raises(EventSequenceError, match="cannot follow a terminal"):
        validator.consume(event(8, "answer.delta", binding_id="binding-1", scope_id="scope-1"))


def test_routing_refusal_terminates_without_retrieval() -> None:
    events = [
        event(1, "answer.accepted"),
        event(2, "inference.bound", binding_id="binding-1"),
        event(
            3,
            "selection.resolved",
            binding_id="binding-1",
            data={"status": "no_match"},
        ),
        event(
            4,
            "answer.refused",
            binding_id="binding-1",
            data={"reason": "no_match"},
        ),
    ]
    validator = AnswerEventSequenceValidator()
    validator.validate(events)

    assert validator.terminal
