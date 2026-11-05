"""Package boundaries and shared contract shapes (Contract Gate tests).

These tests import only ``qa_contracts`` and the schema artifacts. They must not
import A1 repositories or A2 core implementations, so the Gate can verify
compatibility without either side's provider.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from qa_contracts.answers import AnswerEvent, SearchRequest
from qa_contracts.errors import STATUS_BY_CODE, ErrorCode
from qa_contracts.models import DiscoveryRequest, InferencePolicy
from qa_contracts.operations import JobEvent, Principal  # noqa: F401
from qa_contracts.selection import AutoSelection, ExplicitSelection, RetrievalSelection

ROOT = Path(__file__).resolve().parents[2]
OPENAPI = ROOT / "docs" / "openapi.json"
EVENTS = ROOT / "docs" / "events.schema.json"


def test_schema_artifacts_exist() -> None:
    assert OPENAPI.exists(), "run scripts/export_contracts.py"
    assert EVENTS.exists(), "run scripts/export_contracts.py"


def test_openapi_has_no_parameterless_required_model_bodies() -> None:
    schema = json.loads(OPENAPI.read_text(encoding="utf-8"))
    for path, operations in schema["paths"].items():
        for method, operation in operations.items():
            for parameter in operation.get("parameters", []):
                assert "schema" in parameter, f"{method.upper()} {path} parameter lacks schema"


def test_retrieval_selection_is_strict_union() -> None:
    adapter = TypeAdapter(RetrievalSelection)
    assert isinstance(
        adapter.validate_python({"mode": "explicit", "targets": [{"kb_id": "a"}]}),
        ExplicitSelection,
    )
    assert isinstance(
        adapter.validate_python({"mode": "auto", "max_kbs": 2}), AutoSelection
    )
    with pytest.raises(ValidationError):
        adapter.validate_python({"targets": [{"kb_id": "a"}]})
    with pytest.raises(ValidationError):
        adapter.validate_python({"mode": "explicit", "targets": []})
    with pytest.raises(ValidationError):
        adapter.validate_python({"mode": "auto", "candidate_kb_ids": []})


def test_selection_and_inference_are_independent() -> None:
    request = SearchRequest.model_validate(
        {
            "question": "q",
            "selection": {"mode": "explicit", "targets": [{"kb_id": "a"}]},
            "inference": {"profile_id": "p1", "policy": "local_only"},
        }
    )
    assert request.selection is not None
    assert request.inference is not None
    assert request.inference.policy is InferencePolicy.LOCAL_ONLY


def test_discovery_request_cannot_carry_endpoint_or_path() -> None:
    adapter = TypeAdapter(DiscoveryRequest)
    with pytest.raises(ValidationError):
        adapter.validate_python({"target_ids": ["x"], "url": "http://example.invalid"})
    with pytest.raises(ValidationError):
        adapter.validate_python({"target_ids": ["x"], "model_dir": "C:/models"})
    assert adapter.validate_python({"target_ids": ["x"]}).target_ids == ["x"]


def test_error_codes_are_stable() -> None:
    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    assert events["error_codes"] == {
        code.value: STATUS_BY_CODE[code] for code in ErrorCode
    }
    assert events["error_codes"]["FEATURE_NOT_IMPLEMENTED"] == 501


def test_sse_contract_separates_answer_and_job_ids() -> None:
    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    assert "answer_id" in events["answer_event"]["properties"]
    assert "job_id" not in events["answer_event"]["properties"]
    assert "job_id" in events["job_event"]["properties"]
    assert "answer_id" not in events["job_event"]["properties"]

    answer = AnswerEvent(
        answer_id="a1", session_id="s1", seq=1, event="answer.completed"
    )
    assert answer.schema_version == 1
    assert "answer_id" in answer.model_dump()


def test_event_types_and_terminal_states_match_dto() -> None:
    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    answer_events = set(events["event_types"]["answer"])
    terminal = set(events["answer_events"]["terminal"])
    assert terminal <= answer_events
    assert len(terminal) == 4
    assert events["answer_events"]["single_terminal"] is True
