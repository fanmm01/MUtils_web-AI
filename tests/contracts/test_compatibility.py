"""P2 Gate: previously frozen P1 event and routing envelopes stay valid."""

from __future__ import annotations

import json
from pathlib import Path

from qa_contracts.answers import AnswerEvent, SearchRequest
from qa_contracts.knowledge import ImportPreviewRequest, ImportRequest
from qa_contracts.operations import JobEvent
from qa_contracts.selection import ExplicitSelection
from tests.contracts.fixtures import load_fixture

ROOT = Path(__file__).resolve().parents[2]


def test_p1_answer_and_job_event_fixtures_remain_readable() -> None:
    path = ROOT / "Q&A_Assistant/tests/fixtures/answer-events.schema-v1.jsonl"
    events = [
        AnswerEvent.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert [event.seq for event in events] == list(range(1, len(events) + 1))
    assert all(event.schema_version == 1 for event in events)
    assert JobEvent(job_id="j1", seq=1, event="job.accepted").schema_version == 1


def test_p1_search_selection_is_unchanged_by_pinned_response_scope() -> None:
    fixture = load_fixture("search_explicit_single.json")
    request = SearchRequest.model_validate(fixture["body"])
    assert isinstance(request.selection, ExplicitSelection)
    assert request.selection.targets[0].version_id is None
    assert request.top_k == 10


def test_preview_is_non_destructive_and_apply_requires_preview_hash() -> None:
    preview_fixture = load_fixture("import_preview_mirror.json")
    apply_fixture = load_fixture("import_confirm_mirror.json")
    assert ImportPreviewRequest.model_validate(preview_fixture["body"]).mode == "mirror"
    apply = ImportRequest.model_validate(apply_fixture["body"])
    assert apply.mode == "mirror"
    assert apply.expected_preview_hash


def test_exported_events_retain_version_one_and_terminal_states() -> None:
    artifact = json.loads((ROOT / "docs/events.schema.json").read_text(encoding="utf-8"))
    assert artifact["schema_version"] == 1
    assert artifact["http_schema_version"] == 2
    assert artifact["answer_event"]["properties"]["schema_version"]["const"] == 1
    assert set(artifact["answer_events"]["terminal"]) == {
        "answer.completed", "answer.refused", "answer.failed", "answer.cancelled"
    }
