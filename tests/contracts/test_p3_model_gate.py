"""P3 model/vector gate: fake contract checks without model I/O."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import get_type_hints

import pytest
from pydantic import ValidationError

from qa_contracts.answers import GenerationRequest, SearchRequest
from qa_contracts.base import utc_now
from qa_contracts.errors import (
    InferencePolicyViolation,
    ModelCapabilityMissing,
    ModelChanged,
    PermissionDenied,
    ValidationFailed,
)
from qa_contracts.model_ports import ModelInstaller, RuntimeDiscovery, authorize_discovery
from qa_contracts.models import (
    CandidateEmbedder,
    DiscoveryReport,
    DiscoveryRequest,
    EmbeddingProfile,
    ExecutionLocation,
    InferenceBinding,
    InferencePolicy,
    InferenceProfile,
    InstallConfirmation,
    InstallPreview,
    InstallRequest,
    ModelIdentity,
    ModelRole,
    RoleBinding,
    RuntimeKind,
    RuntimeTarget,
    TransferState,
    authorize_role_binding,
)
from qa_contracts.operations import AccessScope
from qa_contracts.ports import Generator, QAServicePort, TokenCounter, VectorIndexWriter
from qa_contracts.repositories import ImportResolutionRepository


def _identity(
    *, digest: str = "sha256:" + "d" * 64, model_id: str = "m1"
) -> ModelIdentity:
    return ModelIdentity(
        model_id=model_id, exact_tag="embedding:latest", digest=digest,
        identity_status="resolved", runtime_target_id="ollama",
    )


def _embedding(**changes: object) -> EmbeddingProfile:
    attributes: dict[str, object] = {
        "profile_key": "embedding-v1", "model_id": "m1", "digest": "sha256:" + "d" * 64,
        "dimension": 1024, "normalized": True, "preprocessing": "unicode-nfc",
        "truncation_tokens": 8192, "truncation_policy": "truncate", "identity": _identity(),
    }
    attributes.update(changes)
    return EmbeddingProfile.model_validate(attributes)


def test_vector_fingerprint_covers_every_pinned_input() -> None:
    reference = _embedding().fingerprint()
    for changes in (
        {"identity": _identity(model_id="m2"), "model_id": "m2"},
        {"identity": _identity(digest="sha256:" + "e" * 64), "digest": "sha256:" + "e" * 64},
        {"dimension": 384}, {"normalized": False}, {"preprocessing": "lowercase"},
        {"truncation_tokens": 4096}, {"truncation_policy": "reject"},
    ):
        assert _embedding(**changes).fingerprint() != reference
    with pytest.raises(ValueError, match="resolved model identity"):
        _embedding(identity=None).fingerprint()
    with pytest.raises(ValidationError, match="identity must match"):
        _embedding(digest="sha256:mismatch")
    with pytest.raises(ValidationError, match="token limit"):
        _embedding(truncation_tokens=None)


def test_identity_tag_drift_or_missing_digest_fails_closed() -> None:
    pinned = _identity()
    pinned.assert_unchanged(_identity())
    with pytest.raises(ModelChanged):
        pinned.assert_unchanged(_identity(digest="sha256:" + "e" * 64))
    with pytest.raises(ModelChanged):
        pinned.assert_unchanged(_identity().model_copy(update={"exact_tag": "other"}))
    with pytest.raises(ValidationError, match="digest"):
        ModelIdentity(model_id="m1", exact_tag="latest", identity_status="resolved")
    with pytest.raises(ValidationError, match="complete sha256"):
        ModelIdentity(model_id="m1", exact_tag="latest", identity_status="resolved", digest="123")
    with pytest.raises(ModelChanged):
        ModelIdentity(model_id="m1", exact_tag="latest").assert_unchanged(pinned)


def test_server_allow_list_and_management_permission_precede_runtime_calls() -> None:
    allowed = [RuntimeTarget(target_id="ollama", kind=RuntimeKind.OLLAMA)]
    manager = AccessScope(principal_id="admin", can_manage_models=True)
    request = DiscoveryRequest(target_ids=["ollama"])
    assert authorize_discovery(request, allowed, manager) == allowed
    with pytest.raises(PermissionDenied):
        authorize_discovery(request, allowed, AccessScope(principal_id="guest"))
    with pytest.raises(ValidationFailed):
        authorize_discovery(DiscoveryRequest(target_ids=["outside"]), allowed, manager)
    with pytest.raises(ValidationError):
        DiscoveryRequest(target_ids=["ollama"], url="https://example.invalid")
    with pytest.raises(ValidationError):
        DiscoveryRequest(target_ids=["ollama"], model_dir="C:/private")
    assert get_type_hints(RuntimeDiscovery.discover)["access"] is AccessScope
    assert get_type_hints(ModelInstaller.preview)["access"] is AccessScope
    assert get_type_hints(ModelInstaller.start)["access"] is AccessScope
    assert get_type_hints(ModelInstaller.start)["idempotency_key"] is str
    assert get_type_hints(ModelInstaller.preview)["request"].__name__ == "InstallRequest"

    class FakeDiscovery:
        def __init__(self) -> None:
            self.probes: list[str] = []

        async def discover(
            self, selected: DiscoveryRequest, targets: list[RuntimeTarget],
            access: AccessScope,
        ) -> DiscoveryReport:
            enabled = authorize_discovery(selected, targets, access)
            self.probes.extend(target.target_id for target in enabled)
            return DiscoveryReport(report_id="rep1", host_id="test-host")

    fake = FakeDiscovery()
    assert isinstance(fake, RuntimeDiscovery)
    with pytest.raises(PermissionDenied):
        asyncio.run(fake.discover(request, allowed, AccessScope(principal_id="guest")))
    assert fake.probes == []
    with pytest.raises(ValidationFailed):
        asyncio.run(fake.discover(DiscoveryRequest(target_ids=["outside"]), allowed, manager))
    assert fake.probes == []
    asyncio.run(fake.discover(request, allowed, manager))
    assert fake.probes == ["ollama"]


def test_role_requirements_and_local_only_guard_are_explicit() -> None:
    profile = InferenceProfile(profile_id="p1", revision="r1")
    with pytest.raises(ModelCapabilityMissing):
        profile.require_role(ModelRole.GENERATOR)
    with pytest.raises(InferencePolicyViolation):
        RoleBinding(
            role=ModelRole.GENERATOR, policy=InferencePolicy.LOCAL_ONLY,
            identity=_identity(), location="configured_remote", runtime_target_id="ollama",
        )
    embedder = RoleBinding(
        role=ModelRole.EMBEDDER, policy=InferencePolicy.LOCAL_ONLY,
        identity=_identity(), runtime_target_id="ollama",
    )
    binding = InferenceBinding(
        binding_id="b1", policy=InferencePolicy.LOCAL_ONLY,
        candidate_embedders=[CandidateEmbedder(
            kb_id="kb1", version_id="v1", fingerprint=_embedding().fingerprint(),
            binding=embedder,
        )],
    )
    assert binding.require_embedder("kb1", "v1").fingerprint == _embedding().fingerprint()
    allowed = [RuntimeTarget(target_id="ollama", kind=RuntimeKind.OLLAMA)]
    assert authorize_role_binding(embedder, allowed, _identity()) == allowed[0]
    with pytest.raises(ModelChanged):
        authorize_role_binding(embedder, allowed, _identity(digest="sha256:" + "e" * 64))
    with pytest.raises(InferencePolicyViolation):
        authorize_role_binding(
            embedder,
            [RuntimeTarget(target_id="ollama", kind=RuntimeKind.OLLAMA,
                           location="configured_remote")],
            _identity(),
        )
    with pytest.raises(ModelCapabilityMissing):
        binding.require_embedder("kb2", "v2")
    with pytest.raises(ModelCapabilityMissing):
        binding.require_role(ModelRole.GENERATOR)
    with pytest.raises(ValidationError, match="policy must match"):
        InferenceBinding(binding_id="b1", policy="configured", roles=[embedder])


def test_preview_expiry_subject_and_unknown_identity_do_not_imply_install_success() -> None:
    request = InstallRequest(target_id="ollama", model_ref="m:latest")
    access = AccessScope(principal_id="operator", can_manage_models=True)
    allowed = [RuntimeTarget(target_id="ollama", kind=RuntimeKind.OLLAMA)]
    assert request.authorize(allowed, access).target_id == "ollama"
    with pytest.raises(PermissionDenied):
        request.authorize(allowed, AccessScope(principal_id="viewer"))
    with pytest.raises(ModelCapabilityMissing):
        request.authorize([], access)
    now = utc_now()
    preview = InstallPreview(
        preview_id="p1", target_id="ollama", target_location=ExecutionLocation.LOCAL,
        model_ref="m:latest", preview_hash="h1", principal_id="operator",
        created_at=now, expires_at=now + timedelta(minutes=5),
        identity_status="unresolved", unknown_fields=["digest", "total_bytes"],
    )
    preview.assert_confirmable("operator", now)
    for principal, instant in (("intruder", now), ("operator", preview.expires_at)):
        with pytest.raises(ValueError, match="expired or belongs"):
            preview.assert_confirmable(principal, instant)
    assert preview.identity_status == "unresolved" and preview.expected_identity is None
    with pytest.raises(ValueError, match="confirmation does not match"):
        preview.assert_confirmable(
            "operator", now, InstallConfirmation(
                preview_id="other", preview_hash="h1", confirmed=True
            ),
        )
    resolved = preview.model_copy(
        update={"identity_status": "resolved", "expected_identity": _identity()}
    )
    resolved.assert_confirmable("operator", now, observed_identity=_identity())
    with pytest.raises(ModelChanged):
        resolved.assert_confirmable(
            "operator", now, observed_identity=_identity(digest="sha256:" + "e" * 64)
        )
    with pytest.raises(ValidationError, match="confirmed terminal"):
        TransferState(handle_id="t1", phase="completed", outcome_unknown=True)
    with pytest.raises(ValidationError):
        InstallPreview.model_validate({
            "preview_id": "p1", "target_id": "ollama",
            "target_location": "local", "model_ref": "m:latest", "preview_hash": "h1",
        })
    with pytest.raises(ValidationError, match="server-owned opaque"):
        InstallPreview.model_validate({
            **preview.model_dump(mode="json"), "target_cache": "C:/private/models",
        })
    with pytest.raises(ValidationError, match="expiry"):
        InstallPreview.model_validate({
            **preview.model_dump(mode="json"),
            "expires_at": (now - timedelta(seconds=1)).isoformat(),
        })


def test_ports_are_typed_without_model_runtime_imports() -> None:
    assert get_type_hints(Generator.stream)["request"] is GenerationRequest
    assert get_type_hints(TokenCounter.count)["request"] is GenerationRequest
    assert get_type_hints(QAServicePort.search)["request"] is SearchRequest
    assert get_type_hints(QAServicePort.search)["binding"] is InferenceBinding
    assert get_type_hints(VectorIndexWriter.build)["profile"] is EmbeddingProfile
    assert "resolve_authorized" in vars(ImportResolutionRepository)
