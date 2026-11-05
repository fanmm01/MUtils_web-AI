"""Model runtime ports: discovery, lifecycle, install transfer and policy guard."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from .models import (
    CancelResult,
    DiscoveryReport,
    InstallPlan,
    InstallPreview,
    ModelQuery,
    ModelRef,
    RoleBinding,
    RuntimeStatus,
    RuntimeTarget,
    TransferHandle,
    TransferState,
)


@runtime_checkable
class RuntimeDiscovery(Protocol):
    async def discover(self, targets: list[RuntimeTarget]) -> DiscoveryReport: ...


@runtime_checkable
class ModelRuntime(Protocol):
    async def probe(self, target: RuntimeTarget) -> RuntimeStatus: ...

    async def list_models(self, target: RuntimeTarget, query: ModelQuery) -> list[ModelRef]: ...

    async def inspect(self, ref: ModelRef) -> ModelRef: ...


@runtime_checkable
class ModelInstaller(Protocol):
    async def preview(self, request: object) -> InstallPreview: ...

    async def start(self, plan: InstallPlan) -> TransferHandle: ...

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
