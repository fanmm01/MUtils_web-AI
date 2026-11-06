"""P3 conflict wire gate; the operational resolver belongs to the later A1 short fix."""

from __future__ import annotations

import json
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from qa_contracts.base import utc_now
from qa_contracts.errors import Conflict, PermissionDenied
from qa_contracts.knowledge import (
    ImportPreview,
    ImportRequest,
    ImportResolution,
    ResolveImportConflicts,
    SearchScope,
    Snapshot,
)
from qa_contracts.models import EmbeddingProfile, ModelIdentity
from qa_contracts.operations import AccessScope


class _FakeResolutionGate:
    """Independent contract consumer; not a substitute for A1's SQLite resolver."""

    def __init__(self) -> None:
        self.preview = ResolveImportConflicts.model_validate(_request())
        self.conflicts = [self.preview.decisions[0]]
        self.source_digest = "sha256:after"
        self.manual_revision = "rev_manual"
        self.active_version = "v1"
        self.expires_at = utc_now() + timedelta(minutes=5)
        self.records: dict[tuple[str, str], tuple[str, ImportResolution]] = {}

    def resolve(
        self, req: ResolveImportConflicts, access: AccessScope, key: str
    ) -> ImportResolution:
        if not access.can_manage_kb or req.kb_id not in access.kb_ids:
            raise PermissionDenied("resolve import conflicts")
        request_hash = req.model_dump_json()
        identity = (access.principal_id, key)
        previous = self.records.get(identity)
        if previous is not None:
            if previous[0] != request_hash:
                raise Conflict("same idempotency body", "different body")
            return previous[1]
        if (
            utc_now() >= self.expires_at or req.preview_id != self.preview.preview_id
            or req.expected_preview_hash != self.preview.expected_preview_hash
            or req.source_id != self.preview.source_id
            or req.expected_active_version_id != self.active_version
            or len(req.decisions) != len(self.conflicts)
            or any(
                decision.source_id != conflict.source_id
                or decision.relative_path != conflict.relative_path
                or decision.document_id != conflict.document_id
                or decision.source_baseline_revision_id != conflict.source_baseline_revision_id
                or decision.source_baseline_digest != conflict.source_baseline_digest
                or decision.manual_revision_id != self.manual_revision
                or decision.incoming_source_digest != self.source_digest
                for decision, conflict in zip(req.decisions, self.conflicts, strict=True)
            )
        ):
            raise Conflict("current preview and revisions", "source or manual state changed")
        record = ImportResolution(
            resolution_id="res1", kb_id=req.kb_id, preview_id=req.preview_id,
            preview_hash=req.expected_preview_hash, source_id=req.source_id,
            principal_id=access.principal_id, request_hash=request_hash,
            expected_active_version_id=req.expected_active_version_id,
            decisions=req.decisions, expires_at=self.expires_at,
        )
        self.records[identity] = (request_hash, record)
        return record


def _decision(strategy: str = "keep_manual") -> dict[str, str]:
    return {
        "strategy": strategy,
        "source_id": "src1",
        "relative_path": "folder/a.md",
        "document_id": "doc1",
        "source_baseline_revision_id": "rev_source",
        "manual_revision_id": "rev_manual",
        "source_baseline_digest": "sha256:before",
        "incoming_source_digest": "sha256:after",
    }


def _request(strategy: str = "keep_manual") -> dict[str, object]:
    return {
        "kb_id": "kb1",
        "source_id": "src1",
        "preview_id": "prev1",
        "expected_preview_hash": "sha256:preview",
        "expected_active_version_id": "v1",
        "decisions": [_decision(strategy)],
    }


@pytest.mark.parametrize("strategy", ["keep_manual", "use_source", "fork_document"])
def test_fake_resolution_is_idempotent_and_bound_to_authorized_preview(strategy: str) -> None:
    gate = _FakeResolutionGate()
    req = ResolveImportConflicts.model_validate(_request(strategy))
    access = AccessScope(principal_id="operator", kb_ids=["kb1"], can_manage_kb=True)
    first = gate.resolve(req, access, "same-key")
    assert gate.resolve(req, access, "same-key").resolution_id == first.resolution_id
    assert first.principal_id == access.principal_id and first.decisions[0].strategy == strategy
    other = "fork_document" if strategy == "use_source" else "use_source"
    with pytest.raises(Conflict):
        gate.resolve(
            ResolveImportConflicts.model_validate(_request(other)), access, "same-key"
        )
    with pytest.raises(PermissionDenied):
        gate.resolve(req, AccessScope(principal_id="viewer", kb_ids=["kb1"]), "new-key")


@pytest.mark.parametrize("drift", ["expired", "manual", "source", "active_version"])
def test_fake_resolution_rejects_stale_or_concurrent_preview(drift: str) -> None:
    gate = _FakeResolutionGate()
    if drift == "expired":
        gate.expires_at = utc_now() - timedelta(seconds=1)
    elif drift == "manual":
        gate.manual_revision = "concurrent-edit"
    elif drift == "source":
        gate.source_digest = "sha256:changed"
    else:
        gate.active_version = "v2"
    with pytest.raises(Conflict):
        gate.resolve(
            ResolveImportConflicts.model_validate(_request()),
            AccessScope(principal_id="operator", kb_ids=["kb1"], can_manage_kb=True),
            "new-key",
        )


@pytest.mark.parametrize("strategy", ["keep_manual", "use_source", "fork_document"])
def test_all_three_decisions_are_discriminated_and_roundtrip(strategy: str) -> None:
    req = ResolveImportConflicts.model_validate(_request(strategy))
    assert req.decisions[0].strategy == strategy
    assert ResolveImportConflicts.model_validate_json(req.model_dump_json()) == req
    record = ImportResolution(
        resolution_id="res1", kb_id="kb1", preview_id=req.preview_id,
        preview_hash=req.expected_preview_hash, source_id="src1",
        principal_id="local-operator", request_hash="sha256:request",
        expires_at=utc_now(),
        expected_active_version_id="v1", decisions=req.decisions,
    )
    restored = ImportResolution.model_validate_json(record.model_dump_json())
    assert restored.decisions[0] == req.decisions[0]


@pytest.mark.parametrize("patch", [
    {"expected_active_version_id": "missing"},
    {"source_id": "other_source"},
    {"expected_preview_hash": ""},
    {"decisions": []},
    {"decisions": [_decision(), _decision("use_source")]},
    {"decisions": [{**_decision(), "strategy": "overwrite"}]},
    {"decisions": [{key: value for key, value in _decision().items()
                    if key != "source_baseline_digest"}]},
    {"decisions": [{**_decision(), "source_baseline_digest": ""}]},
    {"decisions": [{**_decision(), "relative_path": "../escape"}]},
    {"decisions": [{**_decision(), "fork_target_document_id": "client-controlled"}]},
])
def test_incomplete_or_unsafe_decisions_are_rejected(patch: dict[str, object]) -> None:
    body = _request()
    if patch.get("expected_active_version_id") == "missing":
        del body["expected_active_version_id"]
    else:
        body.update(patch)
    with pytest.raises(ValidationError):
        ResolveImportConflicts.model_validate(body)


def test_p2_preview_and_apply_remain_compatible() -> None:
    legacy = ImportPreview.model_validate({
        "preview_id": "p1", "kb_id": "kb1", "preview_hash": "h", "conflicts": ["folder/a.md"],
    })
    assert legacy.conflict_details == []
    old_apply = ImportRequest.model_validate({
        "kb_id": "kb1", "source_id": "src1", "expected_preview_hash": "h",
    })
    assert old_apply.resolution_id is None
    assert old_apply.model_dump(exclude_none=True).get("resolution_id") is None
    assert json.loads(old_apply.model_dump_json(exclude_none=True))["expected_preview_hash"] == "h"


@pytest.mark.parametrize("strategy", ["keep_manual", "use_source", "fork_document"])
def test_resolve_route_is_only_an_explicit_501_contract_placeholder(
    client: TestClient, strategy: str
) -> None:
    response = client.post(
        "/v1/kbs/kb1/imports/prev1/resolve", json=_request(strategy),
        headers={"Idempotency-Key": "key1"},
    )
    assert response.status_code == 501
    assert response.json()["error"]["code"] == "FEATURE_NOT_IMPLEMENTED"


def test_resolve_route_rejects_non_manager_before_business(client: TestClient) -> None:
    from qa_contracts.operations import Principal
    from qa_service.deps import get_principal

    client.app.dependency_overrides[get_principal] = lambda: Principal(principal_id="reader")
    try:
        response = client.post(
            "/v1/kbs/kb1/imports/prev1/resolve", json=_request(),
            headers={"Idempotency-Key": "key1"},
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    finally:
        client.app.dependency_overrides.clear()


def test_resolve_route_requires_key_and_matching_ids(client: TestClient) -> None:
    path = "/v1/kbs/kb1/imports/prev1/resolve"
    assert client.post(path, json=_request()).status_code == 422
    assert client.post(path, json=_request(), headers={"Idempotency-Key": "  "}).status_code == 422
    for mismatched in ({**_request(), "kb_id": "kb2"}, {**_request(), "preview_id": "prev2"}):
        response = client.post(path, json=mismatched, headers={"Idempotency-Key": "key1"})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_vector_snapshot_requires_resolved_identity_and_immutable_ref() -> None:
    legacy = Snapshot(
        version_id="v1", kb_id="kb1", state="ready",
        keyword_profile="bm25", keyword_index_ref="idx1",
    )
    assert legacy.vector_index == "absent" and legacy.vector_index_ref is None
    identity = ModelIdentity(
        model_id="m1", exact_tag="embedding:latest", digest="sha256:" + "a" * 64,
        identity_status="resolved", runtime_target_id="ollama",
    )
    profile = EmbeddingProfile(
        profile_key="e1", model_id="m1", digest=identity.digest,
        identity=identity, dimension=1024, preprocessing="unicode-nfc",
    )
    snapshot = legacy.model_copy(update={
        "version_id": "v2", "vector_index": "present",
        "vector_index_ref": "vector-v2", "embedding_fingerprint": profile,
    })
    assert Snapshot.model_validate(snapshot.model_dump()).embedding_fingerprint == profile
    for changed in (
        {"vector_index_ref": None},
        {"embedding_fingerprint": None},
        {"embedding_fingerprint": profile.model_copy(update={"identity": None})},
        {"embedding_fingerprint": profile.model_copy(update={"dimension": 0})},
    ):
        with pytest.raises(ValidationError):
            Snapshot.model_validate(snapshot.model_copy(update=changed).model_dump())
    scope = SearchScope(
        kb_id="kb1", version_id="v2", keyword_profile="bm25", index_ref="idx1",
        vector_index_ref="vector-v2", embedding_fingerprint=profile,
    )
    assert scope.embedding_fingerprint.fingerprint() == profile.fingerprint()
    with pytest.raises(ValidationError):
        SearchScope.model_validate(scope.model_copy(update={"vector_index_ref": None}).model_dump())


def test_resolution_id_cannot_be_applied_before_resolver_exists(client: TestClient) -> None:
    response = client.post("/v1/kbs/kb1/imports", json={
        "kb_id": "kb1", "source_id": "src1", "expected_preview_hash": "h", "resolution_id": "res1",
    })
    assert response.status_code == 501
    assert response.json()["error"]["code"] == "FEATURE_NOT_IMPLEMENTED"