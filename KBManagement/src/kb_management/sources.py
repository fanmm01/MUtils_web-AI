"""Source registration, scanning and streamed uploads.

Deletion eligibility is *not* decided here: :class:`LocalSource` only reports
what it actually scanned, and marks the scan ``partial`` whenever it was
restricted, unreadable or interrupted. Only a complete, successful full scan can
later authorize removals.
"""

from __future__ import annotations

import hashlib
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from qa_contracts.errors import Conflict, NotFound, PermissionDenied, ValidationFailed
from qa_contracts.knowledge import (
    ManifestFile,
    Selection,
    Source,
    SourceManifest,
    UploadBatch,
    UploadManifest,
)

from .parsers import SUPPORTED_EXTENSIONS, detect_kind

_CHUNK = 1024 * 1024


@dataclass(slots=True)
class SourceRoot:
    root_id: str
    path: Path


def _safe_child(root: Path, relative: str) -> Path:
    """Resolve ``relative`` inside ``root`` and refuse every escape or symlink."""
    try:
        candidate = (root / relative).resolve(strict=True)
    except OSError as exc:
        raise PermissionDenied("read source file") from exc
    if not candidate.is_relative_to(root.resolve()) or candidate.is_symlink():
        raise PermissionDenied("read source file")
    return candidate


class LocalSource:
    """Server-side authorized root; clients never submit absolute paths."""

    def __init__(self, root: SourceRoot, *, max_files: int = 10_000) -> None:
        self.root = root
        self.max_files = max_files

    def _match(self, relative: str, selection: Selection) -> bool:
        import fnmatch

        if selection.relative_paths and relative not in selection.relative_paths:
            return False
        if selection.include_globs and not any(
            fnmatch.fnmatch(relative, pattern) for pattern in selection.include_globs
        ):
            return False
        return not (
            selection.exclude_globs
            and any(fnmatch.fnmatch(relative, pattern) for pattern in selection.exclude_globs)
        )

    async def scan(self, selection: Selection | None = None) -> SourceManifest:
        chosen = selection or Selection()
        if not self.root.path.is_dir():
            raise NotFound("source root")
        files: list[ManifestFile] = []
        diagnostics: list[str] = []
        status = "succeeded"
        interrupted = False
        count = 0
        def scan_error(error: OSError) -> None:
            nonlocal status
            diagnostics.append(f"{error.filename or self.root.path}: could not be scanned")
            status = "failed"

        for directory, dirs, names in os.walk(
            self.root.path, followlinks=False, onerror=scan_error
        ):
            for name in list(dirs):
                directory_path = Path(directory) / name
                if directory_path.is_symlink():
                    relative = directory_path.relative_to(self.root.path).as_posix()
                    diagnostics.append(f"{relative}: symbolic links are not followed")
                    status = "failed"
                    dirs.remove(name)
            for name in sorted(names):
                path = Path(directory) / name
                relative = path.relative_to(self.root.path).as_posix()
                if not self._match(relative, chosen):
                    continue
                if path.is_symlink():
                    diagnostics.append(f"{relative}: symbolic links are not followed")
                    status = "failed"
                    continue
                kind = detect_kind(relative)
                if kind is None or kind not in SUPPORTED_EXTENSIONS:
                    continue
                count += 1
                if count > self.max_files:
                    diagnostics.append(f"scan stopped after {self.max_files} files")
                    interrupted = True
                    break
                try:
                    resolved = path.resolve(strict=True)
                    if not resolved.is_relative_to(self.root.path.resolve(strict=True)):
                        diagnostics.append(f"{relative}: path escapes the authorized root")
                        status = "failed"
                        continue
                    digest = await _digest_file(resolved)
                    files.append(
                        ManifestFile(
                            relative_path=relative, digest=digest,
                            size=resolved.stat().st_size,
                        )
                    )
                except OSError as exc:
                    diagnostics.append(f"{relative}: could not be read ({exc.strerror})")
                    status = "failed"
            if interrupted:
                break
        restricted = bool(
            chosen.include_globs or chosen.exclude_globs or chosen.relative_paths
        )
        if chosen.relative_paths:
            present = {entry.relative_path for entry in files}
            missing = [path for path in chosen.relative_paths if path not in present]
            if missing:
                # A manifest may not claim a selection the scan did not produce.
                raise ValidationFailed(
                    [_detail("relative_paths", f"selected file was not found: {path}")
                     for path in missing]
                )
        return SourceManifest(
            source_id=self.root.root_id,
            selection=chosen,
            files=files,
            scan_scope="partial" if restricted else "full",
            scan_status=status,
            complete=not restricted and status == "succeeded" and not interrupted,
        )


class UploadSource:
    """Server-side verification of a client upload batch.

    Only bytes that match the claimed digest are ever placed under
    ``<upload_root>/<source_id>/``; a mismatch leaves the previous file intact.
    """

    def __init__(
        self,
        *,
        blobs: object,
        uploads: object,
        sources: object,
        upload_root: Path,
        max_bytes: int = 50 * 1024 * 1024,
    ) -> None:
        self._blobs = blobs
        self._uploads = uploads
        self._sources = sources
        self._upload_root = Path(upload_root).resolve()
        self.max_bytes = max_bytes

    async def begin(self, manifest: UploadManifest) -> UploadBatch:
        source = await self._sources.get(manifest.source_id)
        if source.kind != "upload":
            raise ValidationFailed([_detail("source_id", "is not an upload source")])
        batch_id = f"upload_{uuid.uuid4().hex}"
        await self._uploads.begin(
            batch_id,
            manifest.source_id,
            manifest.selection.model_dump(mode="json"),
            [entry.model_dump(mode="json") for entry in manifest.files],
        )
        return UploadBatch(batch_id=batch_id, source_id=manifest.source_id)

    async def write(self, batch_id: str, relative_path: str, stream: BinaryIO) -> None:
        batch = await self._uploads.get(batch_id)
        if batch["finished_at"]:
            raise ValidationFailed([_detail("batch_id", "is already complete")])
        claimed = {
            str(entry["relative_path"]): entry
            for entry in batch["files"]  # type: ignore[union-attr]
        }
        if relative_path not in claimed:
            raise ValidationFailed([_detail("relative_path", "was not declared in the manifest")])
        target = _upload_path(
            self._upload_root,
            str(batch["source_id"]),
            str(claimed[relative_path]["digest"]),
            relative_path,
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.part")
        digest = hashlib.sha256()
        written = 0
        try:
            with temporary.open("wb") as handle:
                while True:
                    chunk = stream.read(_CHUNK)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > self.max_bytes:
                        raise ValidationFailed(
                            [_detail("file", "exceeds the size limit")]
                        )
                    digest.update(chunk)
                    handle.write(chunk)
            expected = claimed[relative_path]
            if digest.hexdigest() != expected["digest"] or written != expected["size"]:
                raise ValidationFailed(
                    [_detail("file", "content does not match the manifest")]
                )
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        await self._uploads.record_part(batch_id, relative_path, digest.hexdigest(), written)

    async def finish(self, batch_id: str) -> SourceManifest:
        """Verify and commit a batch. Repeating it returns the same manifest."""
        batch = await self._uploads.get(batch_id)
        if batch.get("manifest"):
            return SourceManifest.model_validate_json(str(batch["manifest"]))
        declared = {
            str(entry["relative_path"]): (str(entry["digest"]), int(entry["size"]))
            for entry in batch["files"]  # type: ignore[union-attr]
        }
        received = await self._uploads.parts(batch_id)
        missing = sorted(set(declared) - set(received))
        selection = Selection.model_validate(batch["selection"])
        restricted = bool(
            selection.include_globs or selection.exclude_globs or selection.relative_paths
        )
        files = [
            ManifestFile(relative_path=path, digest=digest, size=size)
            for path, (digest, size) in sorted(received.items())
        ]
        manifest = SourceManifest(
            source_id=str(batch["source_id"]),
            selection=selection,
            files=files,
            scan_scope="partial" if restricted else "full",
            scan_status="failed" if missing else "succeeded",
            complete=not missing and not restricted,
        )
        await self._uploads.finish(batch_id, manifest)
        return manifest


class SourceService:
    def __init__(self, *, sources: object) -> None:
        self._sources = sources

    async def register(self, req: Source) -> Source:
        try:
            await self._sources.get(req.source_id)
        except NotFound:
            return await self._sources.put(req, None)
        raise ValidationFailed([_detail("source_id", "already exists")])

    async def get(self, source_id: str) -> Source:
        return await self._sources.get(source_id)

    async def list(self, kb_id: str) -> list[Source]:
        return await self._sources.list(kb_id)

    async def update(self, source_id: str, req: Source) -> Source:
        current = await self._sources.get(source_id)
        if current.source_id != req.source_id:
            raise ValidationFailed([_detail("source_id", "must match the URL")])
        if current.kb_id != req.kb_id:
            raise ValidationFailed([_detail("kb_id", "a source cannot move between bases")])
        if current.revision != req.revision:
            raise Conflict(f"revision {req.revision}", f"revision {current.revision}")
        return await self._sources.put(req, req.revision)

    async def remove(self, source_id: str) -> None:
        # The repository rejects sources with history/upload batches: removing
        # their configuration would orphan the baseline and permit ID reuse.
        await self._sources.remove(source_id)


class DirectoryPoller:
    """Explicit sync tick; it reuses preview/apply instead of a second diff."""

    def __init__(self, *, local: LocalSource, diff: object, apply: object) -> None:
        self._local = local
        self._diff = diff
        self._apply = apply

    async def tick(self, selection: Selection | None = None) -> object:
        manifest = await self._local.scan(selection)
        changes = await self._diff(manifest, selection)
        return await self._apply(manifest, changes)


async def _digest_file(path: Path) -> str:
    import asyncio

    def compute() -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(_CHUNK)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()

    return await asyncio.to_thread(compute)


def _upload_path(root: Path, source_id: str, digest: str, relative_path: str) -> Path:
    """Store verified upload bytes under a source key and immutable digest path."""
    source_key = hashlib.sha256(source_id.encode("utf-8")).hexdigest()
    digest_key = hashlib.sha256(digest.encode("utf-8")).hexdigest()
    target = root / source_key / digest_key / relative_path
    if not target.parent.resolve().is_relative_to(root.resolve()):
        raise ValidationFailed([_detail("relative_path", "escapes upload storage")])
    return target


def _detail(field: str, reason: str):
    from qa_contracts.errors import ErrorDetail

    return ErrorDetail(field=field, reason=reason)
