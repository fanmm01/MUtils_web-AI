"""P3 answer/Job wire contracts: new version never rewrites persisted v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from qa_contracts.answers import (
    AnswerContext,
    HistorySegment,
    PinnedAnswerContext,
    PinnedTurn,
    parse_answer_event,
    validate_answer_event_sequence_v2,
)
from qa_contracts.operations import (
    JobEvent,
    parse_job_event,
    validate_job_event_sequence_v2,
)

ROOT = Path(__file__).resolve().parents[2]
V1_FIXTURE = ROOT / "Q&A_Assistant/tests/fixtures/answer-events.schema-v1.jsonl"


def _answer_event(
    name: str, seq: int, *, binding_id: str | None = None,
    scope_id: str | None = None, data: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 2,
        "answer_id": "a1",
        "session_id": "s1",
        "scope_revision": 2,
        "inference_revision": 4,
        "seq": seq,
        "binding_id": binding_id,
        "scope_id": scope_id,
        "event": name,
        "data": data or {},
    }


def _binding() -> dict[str, object]:
    return {"binding_id": "b1", "policy": "local_only", "roles": []}


def _scope() -> dict[str, object]:
    return {"scope_id": "scope1", "targets": [{"kb_id": "kb1", "version_id": "v1"}]}


def _citation() -> dict[str, object]:
    return {
        "citation_id": "c1", "chunk_id": "ch1", "kb_id": "kb1", "version_id": "v1",
        "revision_id": "r1", "quote": "evidence", "content_hash": "sha256:1",
        "detail_path": "/v1/answers/a1/citations/c1",
    }


def _success_events() -> list[dict[str, object]]:
    return [
        _answer_event("answer.accepted", 1),
        _answer_event("inference.bound", 2, binding_id="b1", data={"binding": _binding()}),
        _answer_event(
            "selection.resolved", 3, binding_id="b1", scope_id="scope1",
            data={"result": {
                "status": "resolved", "mode": "explicit",
                "targets": [{"kb_id": "kb1", "version_id": "v1"}],
            }, "resolved_scope": _scope()},
        ),
        _answer_event(
            "retrieval.completed", 4, binding_id="b1", scope_id="scope1",
            data={"hit_count": 1},
        ),
        _answer_event(
            "citation.ready", 5, binding_id="b1", scope_id="scope1",
            data={"citation": _citation()},
        ),
        _answer_event(
            "answer.delta", 6, binding_id="b1", scope_id="scope1",
            data={"sentence_id": "sentence1", "text": "supported", "citation_ids": ["c1"]},
        ),
        _answer_event(
            "answer.completed", 7, binding_id="b1", scope_id="scope1",
            data={"answer": {
                "answer_id": "a1", "session_id": "s1", "question": "q",
                "status": "completed", "text": "supported", "binding": _binding(),
                "resolved_scope": _scope(), "citations": [_citation()],
            }},
        ),
    ]


def _parse_answer_events(events: list[dict[str, object]]) -> list[object]:
    return [parse_answer_event(event) for event in events]


def _job_event(name: str, seq: int, **extra: object) -> dict[str, object]:
    return {"schema_version": 2, "job_id": "j1", "seq": seq, "event": name, **extra}


def test_persisted_v1_answers_and_jobs_are_still_decoded_as_v1() -> None:
    lines = V1_FIXTURE.read_text(encoding="utf-8").splitlines()
    parsed = [parse_answer_event(json.loads(line)) for line in lines]
    assert [event.schema_version for event in parsed] == [1, 1, 1, 1, 1]
    legacy = JobEvent(job_id="j1", seq=1, event="job.accepted")
    assert parse_job_event(legacy.model_dump()).schema_version == 1
    with pytest.raises((ValueError, ValidationError)):
        parse_job_event(_job_event("job.cancel_requested", 1) | {"schema_version": 1})


def test_new_answer_event_carries_required_revisions_and_binding_timing() -> None:
    events = _parse_answer_events(_success_events())
    validate_answer_event_sequence_v2(events, require_terminal=True)
    assert [event.seq for event in events] == list(range(1, 8))
    assert events[0].binding_id is None and events[0].scope_id is None
    assert events[1].scope_id is None and events[2].scope_id == "scope1"
    broken = _success_events()[0]
    del broken["scope_revision"]
    with pytest.raises(ValidationError):
        parse_answer_event(broken)
    broken = _success_events()[0] | {"binding_id": "early"}
    with pytest.raises(ValidationError):
        parse_answer_event(broken)


@pytest.mark.parametrize("case", [
    "citation_late", "binding_drift", "scope_drift", "revision_drift",
    "duplicate_seq", "post_terminal", "incomplete_delta", "wrong_final_answer",
    "uncited_delta", "early_retrieval", "no_terminal", "json_text_drift",
    "json_citation_drift", "citation_out_of_scope",
])
def test_answer_replay_rejects_unsafe_sequences(case: str) -> None:
    events = _success_events()
    if case == "citation_late":
        events[4], events[5] = events[5], events[4]
        events[4]["seq"], events[5]["seq"] = 5, 6
    elif case == "binding_drift":
        events[5]["binding_id"] = "other"
    elif case == "scope_drift":
        events[5]["scope_id"] = "other"
    elif case == "revision_drift":
        events[5]["inference_revision"] = 5
    elif case == "duplicate_seq":
        events[5]["seq"] = 5
    elif case == "post_terminal":
        events.append(_answer_event(
            "answer.delta", 8, binding_id="b1", scope_id="scope1",
            data={"sentence_id": "s2", "text": "extra", "citation_ids": ["c1"]},
        ))
    elif case == "incomplete_delta":
        events[6] = _answer_event(
            "answer.failed", 7, binding_id="b1", scope_id="scope1",
            data={"reason": "support failed", "incomplete": False},
        )
    elif case == "wrong_final_answer":
        events[6]["data"]["answer"]["answer_id"] = "other"
    elif case == "uncited_delta":
        events[5]["data"]["citation_ids"] = ["unready"]
    elif case == "early_retrieval":
        events[2], events[3] = events[3], events[2]
        events[2]["seq"], events[3]["seq"] = 3, 4
    elif case == "no_terminal":
        events.pop()
    elif case == "json_text_drift":
        events[6]["data"]["answer"]["text"] = "not streamed"
    elif case == "json_citation_drift":
        events[6]["data"]["answer"]["citations"][0]["quote"] = "different"
    elif case == "citation_out_of_scope":
        events[4]["data"]["citation"]["kb_id"] = "other"
    with pytest.raises((ValueError, ValidationError)):
        validate_answer_event_sequence_v2(_parse_answer_events(events), require_terminal=True)


def test_unresolved_scope_can_refuse_without_retrieval() -> None:
    events = _success_events()[:2]
    events += [
        _answer_event(
            "selection.resolved", 3, binding_id="b1",
            data={"result": {"status": "no_match", "mode": "auto"}},
        ),
        _answer_event(
            "answer.refused", 4, binding_id="b1", data={"reason": "no_match"},
        ),
    ]
    validate_answer_event_sequence_v2(_parse_answer_events(events), require_terminal=True)


def test_turn_segments_reject_cross_scope_answers_and_allow_only_user_questions() -> None:
    scope = _scope()
    turn = {
        "turn_id": "t1", "answer_id": "a1", "question": "old user question",
        "answer_text": "historical answer", "segment_id": "seg1", "resolved_scope": scope,
        "scope_revision": 2, "inference_revision": 4,
        "effective_inference": {"selection": {"policy": "local_only"}},
    }
    parsed = PinnedTurn.model_validate(turn)
    segment = HistorySegment(
        segment_id="seg1", resolved_scope=parsed.resolved_scope, turns=[parsed]
    )
    assert AnswerContext(segments=[segment], current_segment_id="seg1").segments[0] == segment
    assert PinnedAnswerContext(
        session_id="s1", scope_revision=2, inference_revision=4,
        resolved_scope=parsed.resolved_scope, current_segment_id="seg1", turns=[parsed],
        carry_user_questions=["still allowed?"],
    ).carry_user_questions == ["still allowed?"]
    with pytest.raises(ValidationError):
        HistorySegment(segment_id="seg2", resolved_scope=parsed.resolved_scope, turns=[parsed])
    with pytest.raises(ValidationError):
        PinnedAnswerContext(
            session_id="s1", scope_revision=2, inference_revision=4,
            resolved_scope=parsed.resolved_scope, current_segment_id="seg2", turns=[parsed],
        )
    with pytest.raises(ValidationError):
        AnswerContext(segments=[segment], current_segment_id="missing")


def test_job_v2_unknown_cancel_stays_nonterminal_until_verified_reconciliation() -> None:
    events = [
        parse_job_event(_job_event("job.accepted", 1)),
        parse_job_event(_job_event("job.progress", 2, bytes_downloaded=64)),
        parse_job_event(_job_event("job.cancel_requested", 3)),
        parse_job_event(_job_event("job.outcome_unknown", 4, diagnostic="reconcile pending")),
    ]
    validate_job_event_sequence_v2(events)
    with pytest.raises(ValueError, match="terminal"):
        validate_job_event_sequence_v2(events, require_terminal=True)
    validate_job_event_sequence_v2(
        [*events, parse_job_event(_job_event("job.completed", 5))], require_terminal=True
    )
    for raw in [
        _job_event("job.outcome_unknown", 1),
        _job_event("job.completed", 1),
        _job_event("job.accepted", 1, progress=1.1),
    ]:
        with pytest.raises((ValueError, ValidationError)):
            validate_job_event_sequence_v2([parse_job_event(raw)], require_terminal=True)
    with pytest.raises(ValidationError):
        parse_job_event(_job_event("job.outcome_unknown", 1))
    with pytest.raises(ValueError):
        validate_job_event_sequence_v2(
            [*events, parse_job_event(_job_event("job.cancelled", 4))]
        )
    with pytest.raises(ValueError):
        validate_job_event_sequence_v2(
            [*events, parse_job_event(_job_event("job.cancelled", 5)),
             parse_job_event(_job_event("job.completed", 6))]
        )


@pytest.mark.parametrize("event_type", ["answer", "job"])
def test_unknown_event_schema_versions_fail_closed(event_type: str) -> None:
    decode = parse_answer_event if event_type == "answer" else parse_job_event
    sample = _success_events()[0] if event_type == "answer" else _job_event("job.accepted", 1)
    for version in (0, 3, None, True, "2"):
        with pytest.raises((ValueError, ValidationError)):
            decode({**sample, "schema_version": version})