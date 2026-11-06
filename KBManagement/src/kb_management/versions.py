"""Snapshot version queries and lifecycle (A1 owner).

Publishing writes and verifies immutable files first, then swaps the active
pointer in one transaction with an ``expected_active`` comparison. A failed
build never changes the active version.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from qa_contracts.errors import NotFound
from qa_contracts.knowledge import Snapshot


@dataclass(slots=True)
class VersionDiff:
    left: str
    right: str
    added: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RetentionReport:
    retained: list[str] = field(default_factory=list)
    eligible: list[str] = field(default_factory=list)
    protected: list[str] = field(default_factory=list)


class VersionService:
    def __init__(self, *, snapshots: object, knowledge: object, publisher: object) -> None:
        self._snapshots = snapshots
        self._knowledge = knowledge
        self._publisher = publisher

    async def list(self, kb_id: str) -> list[Snapshot]:
        await self._knowledge.get(kb_id)
        return await self._snapshots.list(kb_id)

    async def get(self, version_id: str) -> Snapshot:
        return await self._snapshots.get(version_id)

    async def publish(self, version_id: str, expected_active: str | None) -> Snapshot:
        return await self._publisher.publish(version_id, expected_active)

    async def rollback(
        self, kb_id: str, target: str, expected_active: str | None
    ) -> Snapshot:
        return await self._publisher.rollback(kb_id, target, expected_active)

    async def diff(self, left: str, right: str) -> VersionDiff:
        left_snapshot = await self._snapshots.get(left)
        right_snapshot = await self._snapshots.get(right)
        if left_snapshot.kb_id != right_snapshot.kb_id:
            raise NotFound("comparable versions")
        left_map = left_snapshot.document_revisions
        right_map = right_snapshot.document_revisions
        return VersionDiff(
            left=left,
            right=right,
            added=sorted(set(right_map) - set(left_map)),
            modified=sorted(
                document_id
                for document_id in set(left_map) & set(right_map)
                if left_map[document_id] != right_map[document_id]
            ),
            removed=sorted(set(left_map) - set(right_map)),
        )

    async def retain(self, policy: object) -> RetentionReport:
        """Report only; deleting version files needs explicit operator action."""
        del policy
        report = RetentionReport()
        for kb in await self._knowledge.all():
            versions = await self._snapshots.list(kb.kb_id)
            for snapshot in versions:
                target = report.retained
                if snapshot.version_id == kb.active_version_id:
                    target.append(snapshot.version_id)
                else:
                    report.eligible.append(snapshot.version_id)
        return report
