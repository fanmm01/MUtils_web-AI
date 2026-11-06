"""Model runtime ports: discovery, lifecycle, install transfer and policy guard."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from .errors import ErrorDetail, PermissionDenied, ValidationFailed
from .models import (
    AccessScope,
    CancelResult,
    DiscoveryReport,
    DiscoveryRequest,
    InstallConfirmation,
    InstallPlan,
    InstallPreview,
    InstallRequest,
    ModelQuery,
    ModelRef,
    RoleBinding,
    RuntimeStatus,
    RuntimeTarget,
    TransferHandle,
    TransferState,
)


def authorize_discovery(
    request: DiscoveryRequest, targets: list[RuntimeTarget], access: AccessScope
) -> list[RuntimeTarget]:
    """Pure boundary check; adapters receive only configured server-owned IDs."""
    if not access.can_manage_models:
        raise PermissionDenied("model discovery")
    by_id = {target.target_id: target for target in targets if target.configured}
    if len(by_id) != sum(target.configured for target in targets):
        raise ValueError("runtime allow-list must have unique target IDs")
    requested = request.target_ids or list(by_id)
    if len(set(requested)) != len(requested) or any(target not in by_id for target in requested):
        raise ValidationFailed([ErrorDetail(field="target_ids", reason="not allow-listed")])
    return [by_id[target] for target in requested]


@runtime_checkable
class RuntimeDiscovery(Protocol):
    async def discover(
        self, request: DiscoveryRequest, targets: list[RuntimeTarget], access: AccessScope
    ) -> DiscoveryReport: ...


@runtime_checkable
class ModelRuntime(Protocol):
    async def probe(self, target: RuntimeTarget) -> RuntimeStatus: ...

    async def list_models(self, target: RuntimeTarget, query: ModelQuery) -> list[ModelRef]: ...

    async def inspect(self, ref: ModelRef) -> ModelRef: ...


@runtime_checkable
class ModelInstaller(Protocol):
    async def preview(
        self, request: InstallRequest, targets: list[RuntimeTarget], access: AccessScope
    ) -> InstallPreview: ...

    async def start(
        self,
        plan: InstallPlan,
        preview: InstallPreview,
        confirmation: InstallConfirmation,
        access: AccessScope,
        idempotency_key: str,
        request_hash: str,
    ) -> TransferHandle: ...

    def follow(self, handle: TransferHandle) -> AsyncIterator[TransferState]: ...

    async def cancel(self, handle: TransferHandle) -> CancelResult: ...

    async def reconcile(
        self, plan: InstallPlan, handle: TransferHandle | None
    ) -> TransferState: ...

    async def resume(self, plan: InstallPlan, state: TransferState) -> TransferHandle: ...


@runtime_checkable
class InferenceGuard(Protocol):
    """Called before *every* model call; the only place policy is enforced."""

    async def check(self, binding: RoleBinding) -> None: ...
