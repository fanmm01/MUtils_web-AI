"""Import preview/apply and sync diff placeholders (A1 owner).

Deletion is only ever inferred from a complete, successful scan of the same
source scope; a partial manifest never deletes anything.
"""

from __future__ import annotations

from qa_contracts.knowledge import ChangeSet, ImportPreview, ImportRequest, ManifestFile
from qa_contracts.operations import Job

from . import unimplemented


class ImportService:
    async def preview(self, kb_id: str, manifest: list[ManifestFile]) -> ImportPreview:
        raise unimplemented("kb.imports.preview")

    async def apply(self, req: ImportRequest, expected_preview_hash: str) -> Job:
        raise unimplemented("kb.imports.apply")

    async def execute(self, job: Job) -> object:
        raise unimplemented("kb.imports.execute")


class SyncPlanner:
    async def diff(
        self, previous: list[ManifestFile], current: list[ManifestFile], scope: object
    ) -> ChangeSet:
        raise unimplemented("kb.imports.diff")

    async def resolve_conflict(self, request: object) -> ChangeSet:
        raise unimplemented("kb.imports.resolve_conflict")
