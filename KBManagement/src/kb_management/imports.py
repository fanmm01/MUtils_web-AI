"""Import preview and apply (A1 owner).

Preview is read-only: it computes the same change set a later apply would use
and persists the exact source manifest plus a deterministic hash. Apply requires
that hash and re-verifies the manifest, the file set and the file bytes, so a
file changed after the preview produces a 409 instead of a silent overwrite.

Deletion is only inferred from a complete, successful scan of the same source
scope; a partial manifest never deletes anything.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from qa_contracts.errors import (
    Conflict,
    ErrorDetail,
    NotFound,
    ProviderUnavailable,
    ValidationFailed,
)
from qa_contracts.knowledge import (
    ImportPreview,
    ImportPreviewRequest,
    ImportRequest,
    Selection,
    SourceManifest,
)
from qa_contracts.operations import Job, JobCommand, JobKind

from .indexing import BuildRequest, ChangePlanner, IndexBuilder


@dataclass(slots=True)
class SyncResult:
    changes: object
    job: Job | None = None
    diagnostics: list[str] = field(default_factory=list)


def baseline_hash(manifest: SourceManifest | None) -> str:
    """Identity of the baseline a preview was computed against."""
    if manifest is None:
        return ""
    payload = json.dumps(
        [[entry.relative_path, entry.digest, entry.size] for entry in sorted(
            manifest.files, key=lambda item: item.relative_path
        )],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def preview_hash(kb_id: str, manifest: SourceManifest, mode: str) -> str:
    payload = json.dumps(
        {
            "kb_id": kb_id,
            "source_id": manifest.source_id,
            "mode": mode,
            "selection": manifest.selection.model_dump(mode="json"),
            "files": [
                [entry.relative_path, entry.digest, entry.size]
                for entry in sorted(manifest.files, key=lambda item: item.relative_path)
            ],
            "complete": manifest.complete,
            "scan": [manifest.scan_scope, manifest.scan_status],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class ImportService:
    def __init__(
        self,
        *,
        knowledge: object,
        sources: object,
        previews: object,
        jobs: object,
        builder: IndexBuilder | None = None,
        files: FileResolver | None = None,
        local_roots: Mapping[str, Path] | None = None,
        upload_root: Path | None = None,
    ) -> None:
        self._knowledge = knowledge
        self._sources = sources
        self._previews = previews
        self._jobs = jobs
        self._builder = builder
        self._resolver = files or FileResolver({})
        self._local_roots = {key: Path(value) for key, value in (local_roots or {}).items()}
        self._upload_root = Path(upload_root) if upload_root is not None else None

    async def preview(
        self, req: ImportPreviewRequest, manifest: SourceManifest
    ) -> ImportPreview:
        await self._knowledge.get(req.kb_id)
        source = await self._sources.get(req.source_id)
        if source.kb_id != req.kb_id:
            raise ValidationFailed(
                [_detail("source_id", "does not belong to the requested knowledge base")]
            )
        if manifest.source_id != req.source_id:
            raise ValidationFailed([_detail("source_id", "does not match the source")])
        if manifest.selection != req.selection:
            raise ValidationFailed([_detail("selection", "does not match the source manifest")])
        previous = None
        if await self._sources.has_baseline(req.source_id):
            previous = await self._sources.get_manifest(req.source_id, "")
        change = ChangePlanner.diff(previous, manifest, req.mode)
        preview = ImportPreview(
            preview_id=f"prev_{uuid.uuid4().hex}",
            kb_id=req.kb_id,
            preview_hash=preview_hash(req.kb_id, manifest, req.mode),
            added=change.added,
            modified=change.modified,
            removed=change.removed,
            conflicts=[],
        )
        await self._previews.save(
            preview, manifest, mode=req.mode, baseline_hash=baseline_hash(previous)
        )
        return preview

    async def apply(self, req: ImportRequest, manifest: SourceManifest) -> Job:
        if self._builder is None:
            raise ProviderUnavailable(
                "chunking is not configured; set explicit QA_CHUNK_TARGET_TOKENS"
                " and QA_CHUNK_OVERLAP_TOKENS before importing"
            )
        recorded = await self._previews.find(
            req.kb_id, req.source_id, req.expected_preview_hash
        )
        if recorded is None:
            raise NotFound("import preview")
        preview_record, recorded_manifest, mode, recorded_baseline = recorded
        source = await self._sources.get(req.source_id)
        if source.kb_id != req.kb_id:
            raise ValidationFailed(
                [_detail("source_id", "does not belong to the requested knowledge base")]
            )
        if manifest.source_id != req.source_id:
            raise ValidationFailed([_detail("source_id", "does not match the source")])
        if manifest.selection != recorded_manifest.selection or manifest.selection != req.selection:
            raise Conflict("the previewed selection", "a different source selection was submitted")
        if mode != req.mode:
            raise Conflict(f"preview mode {mode}", f"request mode {req.mode}")
        if not _same_files(recorded_manifest, manifest):
            raise Conflict(
                "the previewed file set", "a different file set was submitted"
            )
        if manifest.scan_status != "succeeded":
            raise ValidationFailed([_detail("manifest", "source scan did not succeed")])
        current_baseline = (
            await self._sources.get_manifest(req.source_id, "")
            if await self._sources.has_baseline(req.source_id)
            else None
        )
        if baseline_hash(current_baseline) != recorded_baseline:
            raise Conflict(
                "the previewed source baseline", "another import changed the baseline"
            )
        await self._verify(source, manifest)
        # The job key covers the preview *and* the baseline it was computed
        # against, so a re-confirmation after a real change creates a new job
        # while an exact replay still returns the original one.
        command = JobCommand(
            kind=JobKind.IMPORT,
            payload={
                "kind": "import",
                "kb_id": req.kb_id,
                "source_id": req.source_id,
                "mode": req.mode,
                "preview_id": preview_record.preview_id,
                "preview_hash": preview_record.preview_hash,
                "manifest": manifest.model_dump(mode="json"),
            },
            idempotency_key=(
                preview_record.preview_id + ":" + recorded_baseline
            ),
        )
        return await self._jobs.enqueue(command, f"job_{uuid.uuid4().hex}")

    async def _verify(self, source: object, manifest: SourceManifest) -> None:
        paths = self.file_paths(source, manifest)
        for entry in manifest.files:
            path = paths[entry.relative_path]
            if path.stat().st_size != entry.size:
                raise Conflict(
                    f"{entry.relative_path} size {entry.size}",
                    f"actual size {path.stat().st_size}",
                )
            if await _sha256(path) != entry.digest:
                raise Conflict(
                    f"{entry.relative_path} digest {entry.digest}", "actual digest differs"
                )

    async def scan(self, source: object, selection: Selection) -> SourceManifest:
        """Server-side scan of an authorized source; the client never sends a path."""
        kind = getattr(source, "kind", "")
        source_id = str(getattr(source, "source_id", ""))
        if kind == "local_root":
            root_id = getattr(source, "root_id", None)
            if not root_id or self._local_roots is None or root_id not in self._local_roots:
                raise ValidationFailed(
                    [_detail("root_id", "source root is not configured on this server")]
                )
            from .sources import LocalSource, SourceRoot

            local = LocalSource(SourceRoot(root_id=root_id, path=self._local_roots[root_id]))
            manifest = await local.scan(selection)
            return manifest.model_copy(update={"source_id": source_id})
        if kind == "upload":
            recorded = await self._sources.get_upload_manifest(source_id)
            if recorded is None:
                raise Conflict("a completed upload batch", "no upload has been completed")
            return recorded
        raise ValidationFailed([_detail("source_id", "has an unsupported source kind")])

    def file_paths(
        self, source: object, manifest: SourceManifest
    ) -> dict[str, Path]:
        """Authorized bytes for a verified manifest (local root or upload store)."""
        source_id = str(getattr(source, "source_id", ""))
        if getattr(source, "kind", "") == "upload":
            if self._upload_root is None:
                raise ValidationFailed([_detail("uploads", "upload storage is not configured")])
            root = self._upload_root / _source_key(source_id)
            return self._resolve_under(root, manifest)
        root_id = getattr(source, "root_id", None)
        if root_id is not None and str(root_id) in self._local_roots:
            root = self._local_roots[str(root_id)]
            return FileResolver({source_id: root}).resolve(source_id, manifest)
        # A resolver injected with an authorized path for this source id is an
        # equally explicit authorization; it never accepts a client path.
        return self._resolver.resolve(source_id, manifest)

    @staticmethod
    def _resolve_under(root: Path, manifest: SourceManifest) -> dict[str, Path]:
        authorized = root.resolve()
        resolved: dict[str, Path] = {}
        for entry in manifest.files:
            try:
                candidate = (
                    root / _upload_digest_key(entry.digest) / entry.relative_path
                ).resolve(strict=True)
            except OSError as exc:
                raise Conflict(
                    f"uploaded bytes for {entry.relative_path}",
                    "the verified upload file is missing",
                ) from exc
            if not candidate.is_relative_to(authorized) or candidate.is_symlink():
                raise ValidationFailed(
                    [_detail("relative_path", "escapes the authorized source root")]
                )
            resolved[entry.relative_path] = candidate
        return resolved

    async def sync(self, source: object, selection: Selection, mode: str = "merge") -> Job:
        """Poll-style sync: scan, preview and enqueue in one server-side action."""
        source_id = str(getattr(source, "source_id", ""))
        kb_id = str(getattr(source, "kb_id", ""))
        manifest = await self.scan(source, selection)
        if manifest.scan_status != "succeeded":
            raise Conflict("a successful scan", "the source scan failed")
        preview = await self.preview(
            ImportPreviewRequest(
                kb_id=kb_id, source_id=source_id, mode=mode, selection=selection
            ),
            manifest,
        )
        return await self.apply(
            ImportRequest(
                kb_id=kb_id,
                source_id=source_id,
                mode=mode,
                selection=selection,
                expected_preview_hash=preview.preview_hash,
            ),
            manifest,
        )

    async def execute(
        self,
        job: Job,
        *,
        files: Mapping[str, Path],
        should_cancel: Callable[[], Awaitable[bool]] | None = None,
    ) -> object:
        payload = await self._jobs.payload(job.job_id)
        if payload.get("kind") != "import":
            raise ValidationFailed([_detail("job", "is not an import job")])
        if self._builder is None:
            raise ProviderUnavailable("chunking is not configured for import execution")
        manifest = SourceManifest.model_validate(payload["manifest"])
        return await self._builder.build(
            BuildRequest(
                kb_id=str(payload["kb_id"]),
                source_id=str(payload["source_id"]),
                manifest=manifest,
                files=files,
                mode=str(payload["mode"]),
                should_cancel=should_cancel,
            )
        )


class FileResolver:
    """Authorized file locations for a verified source manifest."""

    def __init__(self, roots: Mapping[str, Path]) -> None:
        self._roots = {key: Path(value) for key, value in roots.items()}

    @staticmethod
    def default_roots(roots: Mapping[str, Path]) -> dict[str, Path]:
        """Source IDs may differ from their root IDs; the composition root adds both."""
        return {key: Path(value) for key, value in roots.items()}

    def with_source(self, source_id: str, root: Path) -> FileResolver:
        merged = dict(self._roots)
        merged[source_id] = Path(root)
        return FileResolver(merged)

    def resolve(self, source_id: str, manifest: SourceManifest) -> dict[str, Path]:
        root = self._roots.get(source_id)
        if root is None:
            raise ValidationFailed([_detail("source_id", "has no authorized local root")])
        authorized = root.resolve()
        resolved: dict[str, Path] = {}
        for entry in manifest.files:
            try:
                candidate = (root / entry.relative_path).resolve(strict=True)
            except OSError as exc:
                raise Conflict(
                    f"file {entry.relative_path}", "file disappeared after the scan"
                ) from exc
            if not candidate.is_relative_to(authorized) or candidate.is_symlink():
                raise ValidationFailed(
                    [_detail("relative_path", "escapes the authorized source root")]
                )
            resolved[entry.relative_path] = candidate
        return resolved

    async def verify_manifest(self, manifest: SourceManifest) -> None:
        resolved = self.resolve(manifest.source_id, manifest)
        for entry in manifest.files:
            path = resolved[entry.relative_path]
            if path.stat().st_size != entry.size:
                raise Conflict(
                    f"{entry.relative_path} size {entry.size}",
                    f"actual size {path.stat().st_size}",
                )
            digest = await _sha256(path)
            if digest != entry.digest:
                raise Conflict(
                    f"{entry.relative_path} digest {entry.digest}", f"actual {digest}"
                )


def _source_key(source_id: str) -> str:
    return hashlib.sha256(source_id.encode("utf-8")).hexdigest()


def _upload_digest_key(digest: str) -> str:
    return hashlib.sha256(digest.encode("utf-8")).hexdigest()


async def _sha256(path: Path) -> str:
    import asyncio

    def compute() -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()

    return await asyncio.to_thread(compute)


def _same_files(recorded: SourceManifest, submitted: SourceManifest) -> bool:
    recorded_files = {
        entry.relative_path: (entry.digest, entry.size) for entry in recorded.files
    }
    submitted_files = {
        entry.relative_path: (entry.digest, entry.size) for entry in submitted.files
    }
    return recorded_files == submitted_files


def _detail(field: str, reason: str) -> ErrorDetail:
    return ErrorDetail(field=field, reason=reason)


__all__ = ["FileResolver", "ImportService", "SyncResult", "preview_hash"]
