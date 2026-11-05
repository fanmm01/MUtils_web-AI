"""Ollama runtime adapter placeholder.

Discovery is read-only: it never starts the runtime, loads a model or downloads
weights. The concrete protocol work lands in P3 against a verified version.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from qa_contracts.models import (
    CancelResult,
    DiscoveryReport,
    InstallPlan,
    InstallPreview,
    ModelQuery,
    ModelRef,
    RuntimeStatus,
    RuntimeTarget,
    TransferHandle,
    TransferState,
)

from . import unimplemented


class OllamaDiscovery:
    async def discover(self, targets: list[RuntimeTarget]) -> DiscoveryReport:
        raise unimplemented("infrastructure.ollama.discovery")


class OllamaRuntime:
    async def probe(self, target: RuntimeTarget) -> RuntimeStatus:
        raise unimplemented("infrastructure.ollama.probe")

    async def list_models(self, target: RuntimeTarget, query: ModelQuery) -> list[ModelRef]:
        raise unimplemented("infrastructure.ollama.list_models")

    async def inspect(self, ref: ModelRef) -> ModelRef:
        raise unimplemented("infrastructure.ollama.inspect")


class OllamaInstaller:
    async def preview(self, request: object) -> InstallPreview:
        raise unimplemented("infrastructure.ollama.preview")

    async def start(self, plan: InstallPlan) -> TransferHandle:
        raise unimplemented("infrastructure.ollama.start")

    def follow(self, handle: TransferHandle) -> AsyncIterator[TransferState]:
        raise unimplemented("infrastructure.ollama.follow")

    async def cancel(self, handle: TransferHandle) -> CancelResult:
        raise unimplemented("infrastructure.ollama.cancel")

    async def reconcile(
        self, plan: InstallPlan, handle: TransferHandle | None
    ) -> TransferState:
        raise unimplemented("infrastructure.ollama.reconcile")

    async def resume(self, plan: InstallPlan, state: TransferState) -> TransferHandle:
        raise unimplemented("infrastructure.ollama.resume")
