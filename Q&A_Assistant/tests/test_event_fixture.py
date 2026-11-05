from __future__ import annotations

import json
from pathlib import Path

from qa_assistant.events import AnswerEventSequenceValidator
from qa_contracts.answers import AnswerEvent


def test_versioned_answer_event_fixture_is_valid_contract_data() -> None:
    fixture = Path(__file__).parent / "fixtures" / "answer-events.schema-v1.jsonl"
    lines = fixture.read_text(encoding="utf-8").splitlines()
    events = [AnswerEvent.model_validate_json(line) for line in lines if line.strip()]

    assert all(
        json.loads(line)["schema_version"] == 1 for line in lines if line.strip()
    )
    validator = AnswerEventSequenceValidator()
    validator.validate(events)
    assert validator.terminal
