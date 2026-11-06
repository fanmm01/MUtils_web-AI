"""Repository and transaction ports (write side).

All entity parameters use the DTOs above; write operations are constrained by a
unit-of-work transaction. Implementations live in ``Infrastructure``.
"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Protocol

from .answers import Answer, AnswerEvent, AnswerEventV2, SubmitAnswer, Turn
from .base import ID, Page
from .knowledge import (
    ImportResolution,
    KnowledgeBase,
    ResolveImportConflicts,
    Revision,
    Snapshot,
    Source,
    SourceManifest,
)
from .models import (
    AccessScope,
    BindingOwner,
    CallResult,
    DiscoveryReport,
    EffectiveInference,
    InferenceBinding,
    InferenceProfile,
    InstallPreview,
    ModelCall,
    ModelRef,
    ModelVerification,
    ProfileSummary,
    RuntimeStatus,
    TransferState,
    UsageSummary,
)
from .operations import Feedback, Issue, Job, JobCommand, JobEvent, JobEventV2, Principal
from .selection import (
    HistoryPolicy,
    PreparedSelection,
    RetrievalSelection,
    SelectionResult,
)


class UnitOfWork(Protocol):
    def transaction(self) -> AbstractAsyncContextManager[UnitOfWork]: ...


class KnowledgeRepository(Protocol):
    async def get(self, kb_id: ID) -> KnowledgeBase: ...

    async def list(self, limit: int = 50, cursor: str | None = None) -> Page[KnowledgeBase]: ...

    async def put(self, kb: KnowledgeBase, expected_etag: str | None) -> KnowledgeBase: ...

    async def delete(self, kb_id: ID, expected_etag: str | None) -> None: ...


class SourceRepository(Protocol):
    async def get(self, source_id: ID) -> Source: ...

    async def list(self, kb_id: ID) -> list[Source]: ...

    async def put(self, source: Source, expected_revision: ID | None) -> Source: ...

    async def remove(self, source_id: ID) -> None: ...

    async def get_manifest(self, source_id: ID, version_id: ID) -> SourceManifest: ...

    async def save_manifest(
        self, source_id: ID, version_id: ID, manifest: SourceManifest
    ) -> None: ...


class ContentRepository(Protocol):
    async def get(self, document_id: ID, revision_id: ID | None) -> object: ...

    async def append_revision(
        self, document_id: ID, revision: Revision, expected_revision: ID | None
    ) -> Revision: ...


class ImportResolutionRepository(Protocol):
    """Persist one authorized, immutable decision set for a confirmed preview."""

    async def resolve_authorized(
        self,
        request: ResolveImportConflicts,
        access: AccessScope,
        idempotency_key: str,
    ) -> ImportResolution: ...

    async def get_authorized(
        self, resolution_id: ID, principal_id: ID, kb_id: ID, source_id: ID,
    ) -> ImportResolution: ...


class SnapshotRepository(Protocol):
    async def get(self, version_id: ID) -> Snapshot: ...

    async def list(self, kb_id: ID) -> list[Snapshot]: ...

    async def save(self, snapshot: Snapshot) -> None: ...

    async def compare_and_swap_active(
        self, kb_id: ID, expected_active: ID | None, target: ID
    ) -> bool: ...


class ConversationRepository(Protocol):
    async def get_session(self, session_id: ID) -> object: ...

    async def get_answer(self, answer_id: ID) -> Answer: ...

    async def create_session(self, session: object) -> object: ...

    async def update_selection(
        self,
        session_id: ID,
        selection: RetrievalSelection,
        history_policy: HistoryPolicy,
        expected_scope_revision: int,
    ) -> object: ...

    async def update_inference(
        self, session_id: ID, inference: object, expected_inference_revision: int
    ) -> object: ...

    async def list_turns(self, session_id: ID) -> list[Turn]: ...

    async def find_idempotent(
        self, principal_id: ID, operation: str, key: str
    ) -> Answer | None: ...

    async def accept_answer(
        self,
        session_id: ID,
        request: SubmitAnswer,
        effective_selection: RetrievalSelection,
        scope_revision: int,
        effective_inference: EffectiveInference,
        inference_revision: int,
        key: str,
        request_hash: str,
    ) -> Answer: ...

    async def bind_inference(
        self,
        answer_id: ID,
        prepared: PreparedSelection,
        binding: InferenceBinding,
        expected_state: str,
    ) -> Answer: ...

    async def bind_scope(
        self, answer_id: ID, result: SelectionResult, expected_state: str
    ) -> Answer: ...

    async def append_event(
        self, answer_id: ID, event: AnswerEvent | AnswerEventV2
    ) -> AnswerEvent | AnswerEventV2: ...

    async def read_events(
        self, answer_id: ID, after: int, limit: int
    ) -> list[AnswerEvent | AnswerEventV2]: ...

    async def finalize_answer(
        self, answer_id: ID, result: Answer, expected_state: str
    ) -> Answer: ...


class JobRepository(Protocol):
    async def enqueue(self, command: JobCommand, key: str) -> Job: ...

    async def get(self, job_id: ID) -> Job: ...

    async def claim(self, kind: str, worker_id: str, lease_until: object) -> Job | None: ...

    async def renew_lease(self, job_id: ID, worker_id: ID, lease_until: object) -> bool: ...

    async def update_with_event(
        self, job: Job, expected_revision: int, event: JobEvent | JobEventV2
    ) -> Job: ...

    async def update(self, job: Job, expected_revision: int) -> Job: ...

    async def recover(self, now: object) -> list[Job]: ...

    async def find_active_transfer(self, target_key: str) -> Job | None: ...

    async def save_transfer(
        self, job_id: ID, state: TransferState, expected_revision: int
    ) -> Job: ...

    async def append_event(
        self, job_id: ID, event: JobEvent | JobEventV2
    ) -> JobEvent | JobEventV2: ...

    async def read_events(
        self, job_id: ID, after: int, limit: int
    ) -> list[JobEvent | JobEventV2]: ...


class ModelRepository(Protocol):
    async def list_runtimes(self) -> list[RuntimeStatus]: ...

    async def save_discovery(self, report: DiscoveryReport) -> None: ...

    async def get_model(self, model_id: ID) -> ModelRef: ...

    async def list_models(self, query: object) -> Page[ModelRef]: ...

    async def save_model(self, model: ModelRef) -> None: ...

    async def get_profile(self, profile_id: ID, revision: ID | None) -> InferenceProfile: ...

    async def list_profiles(self, access: AccessScope) -> Page[ProfileSummary]: ...

    async def put_profile(
        self, profile: InferenceProfile, expected_revision: ID | None
    ) -> InferenceProfile: ...

    async def disable_profile(self, profile_id: ID, expected_revision: ID) -> InferenceProfile: ...

    async def save_preview(self, preview: InstallPreview) -> None: ...

    async def get_preview(self, preview_id: ID) -> InstallPreview: ...

    async def save_verification(self, result: ModelVerification) -> None: ...

    async def save_binding(self, owner: BindingOwner, binding: InferenceBinding) -> None: ...

    async def get_binding(self, binding_id: ID) -> InferenceBinding: ...


class ModelCallRepository(Protocol):
    async def begin(self, call: ModelCall) -> ModelCall: ...

    async def get(self, call_id: ID) -> ModelCall: ...

    async def finish(self, call_id: ID, result: CallResult, expected_state: str) -> ModelCall: ...

    async def mark_unknown(self, call_id: ID, reason: str) -> ModelCall: ...

    async def summarize(self, owner: BindingOwner) -> UsageSummary: ...


class FeedbackRepository(Protocol):
    async def upsert(self, feedback: Feedback) -> Feedback: ...

    async def create_issue(self, issue: Issue) -> Issue: ...

    async def get_issue(self, issue_id: ID) -> Issue: ...

    async def list_issues(self, query: object) -> Page[Issue]: ...

    async def update_issue(self, issue: Issue, expected_revision: int) -> Issue: ...


class PrincipalRepository(Protocol):
    async def get(self, principal_id: ID) -> Principal: ...
