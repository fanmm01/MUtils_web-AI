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
from qa_contracts.knowledge import (
    ChunkProfile,
    ImportPreviewRequest,
    ImportRequest,
    SearchScope,
    Snapshot,
    SourceManifest,
    UploadManifest,
)
from qa_contracts.models import DiscoveryRequest, InferencePolicy
from qa_contracts.operations import JobEvent, Principal  # noqa: F401
from qa_contracts.selection import (
    AutoSelection,
    ExplicitSelection,
    ResolvedScope,
    RetrievalSelection,
    SelectionResult,
)

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


def test_event_schema_version_rejects_unsupported_values() -> None:
    with pytest.raises(ValidationError):
        AnswerEvent(
            answer_id="a1", session_id="s1", seq=1,
            event="answer.completed", schema_version=99,
        )
    with pytest.raises(ValidationError):
        JobEvent(job_id="j1", seq=1, event="job.completed", schema_version=99)


def test_import_preview_and_apply_are_separate_contracts() -> None:
    preview = ImportPreviewRequest(kb_id="kb", source_id="source", mode="mirror")
    assert preview.mode == "mirror"
    with pytest.raises(ValidationError):
        ImportRequest(kb_id="kb", source_id="source", mode="mirror")
    with pytest.raises(ValidationError):
        ImportRequest(kb_id="kb", source_id="source", expected_preview_hash="")
    confirmed = ImportRequest(
        kb_id="kb", source_id="source", mode="mirror", expected_preview_hash="sha256:preview"
    )
    assert confirmed.expected_preview_hash == "sha256:preview"


def test_only_a_successful_full_server_scan_can_be_complete() -> None:
    with pytest.raises(ValidationError):
        SourceManifest(source_id="source", scan_scope="full", scan_status="succeeded")
    with pytest.raises(ValidationError):
        SourceManifest(
            source_id="source", scan_scope="partial", scan_status="succeeded", complete=True
        )
    with pytest.raises(ValidationError):
        SourceManifest(source_id="source", scan_scope="full", scan_status="failed", complete=True)
    with pytest.raises(ValidationError):
        SourceManifest(
            source_id="source", scan_scope="full", scan_status="succeeded", complete=True,
            selection={"relative_paths": ["only.md"]},
        )
    assert SourceManifest(
        source_id="source", scan_scope="full", scan_status="succeeded", complete=True
    ).files == []  # A verified empty full scan can legitimately be complete.
    with pytest.raises(ValidationError):
        UploadManifest(source_id="source", complete=True)


def test_resolved_scope_requires_unique_versioned_targets() -> None:
    for targets in ([], [{"kb_id": "kb"}], [
        {"kb_id": "kb", "version_id": "v1"}, {"kb_id": "kb", "version_id": "v2"},
    ]):
        with pytest.raises(ValidationError):
            ResolvedScope(scope_id="scope", targets=targets)
    valid = ResolvedScope(scope_id="scope", targets=[{"kb_id": "kb", "version_id": "v1"}])
    assert valid.targets[0].version_id == "v1"


def test_manifest_paths_cannot_escape_selected_root() -> None:
    paths = (
        "../outside.txt",
        "folder/../../outside.txt",
        "/etc/passwd",
        "C:/secret.txt",
        "folder\\\\file.txt",
    )
    for path in paths:
        with pytest.raises(ValidationError):
            UploadManifest.model_validate({
                "source_id": "source",
                "files": [{"relative_path": path, "digest": "sha256:x", "size": 1}],
            })
    safe = UploadManifest.model_validate({
        "source_id": "source",
        "selection": {"relative_paths": ["docs/install.md"]},
        "files": [{"relative_path": "docs/install.md", "digest": "sha256:x", "size": 1}],
    })
    assert safe.files[0].relative_path == "docs/install.md"
    assert safe.selection.relative_paths == ["docs/install.md"]
    with pytest.raises(ValidationError):
        UploadManifest.model_validate({
            "source_id": "source",
            "selection": {"relative_paths": ["docs/other.md"]},
            "files": [{"relative_path": "docs/install.md", "digest": "sha256:x", "size": 1}],
        })
    with pytest.raises(ValidationError):
        UploadManifest.model_validate({
            "source_id": "source",
            "selection": {"relative_paths": ["../outside.md"]},
            "files": [{"relative_path": "docs/install.md", "digest": "sha256:x", "size": 1}],
        })


def test_chunk_profile_rejects_overlap_at_or_above_target() -> None:
    with pytest.raises(ValidationError):
        ChunkProfile(target_tokens=10)
    with pytest.raises(ValidationError):
        ChunkProfile(target_tokens=10, overlap_tokens=10)
    assert ChunkProfile(target_tokens=10, overlap_tokens=9).target_tokens == 10


def test_resolved_selection_targets_and_snapshot_index_are_consistent() -> None:
    for status, targets in (
        ("resolved", []),
        ("resolved", [{"kb_id": "kb"}]),
        ("no_match", [{"kb_id": "kb", "version_id": "v1"}]),
        ("resolved", [
            {"kb_id": "kb", "version_id": "v1"},
            {"kb_id": "kb", "version_id": "v2"},
        ]),
    ):
        with pytest.raises(ValidationError):
            SelectionResult(status=status, mode="auto", targets=targets)
    result = SelectionResult(
        status="resolved", mode="explicit", targets=[{"kb_id": "kb", "version_id": "v1"}]
    )
    assert result.targets[0].version_id == "v1"

    with pytest.raises(ValidationError):
        Snapshot(version_id="v1", kb_id="kb", state="ready")
    snapshot = Snapshot(
        version_id="v1", kb_id="kb", state="ready",
        keyword_profile="zh-v1", keyword_index_ref="sha256:index",
    )
    scope = SearchScope(
        kb_id=snapshot.kb_id, version_id=snapshot.version_id,
        keyword_profile=snapshot.keyword_profile, index_ref=snapshot.keyword_index_ref,
    )
    assert scope.version_id == result.targets[0].version_id


def test_p3_openapi_exports_real_error_binary_replay_and_reserved_sse() -> None:
    schema = json.loads(OPENAPI.read_text(encoding="utf-8"))
    components = schema["components"]["schemas"]
    assert {
        "APIErrorResponse", "ErrorBody", "ErrorDetail", "VersionDiff", "JobEventEnvelope"
    } <= set(components)
    for path, operations in schema["paths"].items():
        for operation in operations.values():
            responses = operation["responses"]
            for status in ("401", "403", "404", "409", "410", "422", "429", "500", "501"):
                if status == "503" and path == "/readyz":
                    continue
                assert responses[status]["content"]["application/json"]["schema"] == {
                    "$ref": "#/components/schemas/APIErrorResponse"
                }
    assert schema["paths"]["/readyz"]["get"]["responses"]["503"]["content"][
        "application/json"
    ]["schema"]["$ref"] == "#/components/schemas/Readiness"
    upload = schema["paths"]["/v1/uploads/{batch_id}/files"]["put"]
    assert upload["requestBody"]["content"]["application/octet-stream"]["schema"][
        "format"
    ] == "binary"
    job = schema["paths"]["/v1/jobs/{job_id}/events"]["get"]
    assert job["responses"]["200"]["content"]["application/json"]["schema"]["items"] == {
        "$ref": "#/components/schemas/JobEventEnvelope"
    }
    assert "text/event-stream" in job["responses"]["200"]["content"]
    assert "text/event-stream" in schema["paths"]["/v1/answers/{answer_id}/events"][
        "get"
    ]["responses"]["200"]["content"]
    assert schema["paths"]["/v1/kbs/{kb_id}/version-diff"]["get"]["responses"][
        "200"
    ]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/VersionDiff"


def test_p3_events_advertise_versions_without_changing_legacy_v1() -> None:
    artifact = json.loads(EVENTS.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == 1
    assert artifact["legacy_schema_version"] == 1
    assert artifact["latest_schema_version"] == 2
    assert artifact["available_versions"] == {"answer": [1, 2], "job": [1, 2]}
    assert artifact["answer_event"]["properties"]["schema_version"]["const"] == 1
    assert artifact["job_event"]["properties"]["schema_version"]["const"] == 1
    assert "job.cancel_requested" not in artifact["event_types"]["job"]
    assert "job.cancel_requested" in artifact["event_types_v2"]["job"]
    assert artifact["answer_event_v2"]["discriminator"]["propertyName"] == "event"


def test_event_types_and_terminal_states_match_dto() -> None:
    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    answer_events = set(events["event_types"]["answer"])
    terminal = set(events["answer_events"]["terminal"])
    assert terminal <= answer_events
    assert len(terminal) == 4
    assert events["answer_events"]["single_terminal"] is True
