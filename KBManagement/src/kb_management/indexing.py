"""Incremental snapshot building placeholder (A2 owner for vector parts).

A build writes a complete, verifiable snapshot and only then allows the active
pointer to move. Failures leave the previous version serving.
"""

from __future__ import annotations

from qa_contracts.knowledge import ChangeSet, Snapshot

from . import unimplemented


class ReusePlan:
    def __init__(self) -> None:
        self.reused_chunk_ids: list[str] = []
        self.reparsed_paths: list[str] = []
        self.reembedded_chunk_ids: list[str] = []


class ValidationReport:
    def __init__(self) -> None:
        self.ok = False
        self.problems: list[str] = []


class IndexBuilder:
    def build(self, change: ChangeSet, base: Snapshot | None) -> Snapshot:
        raise unimplemented("kb.indexing.build")

    def reuse_unchanged(self, change: ChangeSet, base: Snapshot | None) -> ReusePlan:
        raise unimplemented("kb.indexing.reuse_unchanged")

    def validate(self, staged: Snapshot) -> ValidationReport:
        raise unimplemented("kb.indexing.validate")
