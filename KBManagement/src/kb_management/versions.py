"""Snapshot version state machine placeholder (A1 owner).

Publishing writes and verifies immutable files first, then swaps the active
pointer in one transaction with an ``expected_active`` comparison. A failed
build never changes the active version.
"""

from __future__ import annotations

from qa_contracts.knowledge import Snapshot

from . import unimplemented


class VersionService:
    async def list(self, kb_id: str) -> list[Snapshot]:
        raise unimplemented("kb.versions.list")

    async def get(self, version_id: str) -> Snapshot:
        raise unimplemented("kb.versions.get")

    async def publish(self, version_id: str, expected_active: str | None) -> Snapshot:
        raise unimplemented("kb.versions.publish")

    async def rollback(self, kb_id: str, target: str, expected_active: str | None) -> Snapshot:
        raise unimplemented("kb.versions.rollback")

    async def diff(self, left: str, right: str) -> object:
        raise unimplemented("kb.versions.diff")

    async def retain(self, policy: object) -> object:
        raise unimplemented("kb.versions.retain")
