"""Client-side file collection for uploads.

The client sends a manifest and bytes; the server re-validates and decides what
is published or deleted. Paths here are client-local, never server paths.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from pathlib import Path

from .client import Client


def collect_upload(
    root: Path, relative_paths: Iterable[str] | None = None
) -> list[dict[str, object]]:
    """Build a manifest of regular files under ``root`` (sorted, path-stable)."""
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("upload root must be a directory")
    wanted = set(relative_paths) if relative_paths is not None else None
    manifest: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.resolve(strict=True).is_relative_to(root):
            raise ValueError("upload directory must not contain symlinks or escaped paths")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if wanted is not None and relative not in wanted:
            continue
        data = path.read_bytes()
        manifest.append(
            {"relative_path": relative, "digest": hashlib.sha256(data).hexdigest(),
             "size": len(data)}
        )
    if wanted is not None and wanted != {str(item["relative_path"]) for item in manifest}:
        raise ValueError("requested upload files were not found under the root")
    return manifest


def upload_directory(
    client: Client,
    root: Path,
    selection: Mapping[str, object] | None = None,
    *,
    source_id: str,
    kb_id: str | None = None,
) -> dict[str, object]:
    """Upload a manifest and its bytes; stop on the first failed or changed file.

    With ``kb_id`` the client also previews and applies the import, returning the
    preview (with ``job_id``) so the caller can watch the job. The server still
    owns every scan, deletion and publish decision.
    """
    if not source_id:
        raise ValueError("source_id is required")
    relative_paths = selection.get("relative_paths") if selection else None
    if relative_paths is not None and (
        isinstance(relative_paths, (str, bytes)) or not isinstance(relative_paths, list)
        or any(not isinstance(path, str) for path in relative_paths)
    ):
        raise ValueError("relative_paths must be a list of paths")
    if selection and (selection.get("include_globs") or selection.get("exclude_globs")):
        raise ValueError("upload_directory supports explicit relative_paths only")
    root = root.resolve(strict=True)
    manifest = collect_upload(root, relative_paths)
    batch = client._post(
        "/v1/uploads",
        json={"source_id": source_id, "selection": dict(selection or {}), "files": manifest},
    )
    batch_id = batch.get("batch_id") if isinstance(batch, dict) else None
    if not isinstance(batch_id, str) or not batch_id:
        raise RuntimeError("upload batch was not accepted")
    for item in manifest:
        path = root / str(item["relative_path"])
        if path.is_symlink() or not path.resolve(strict=True).is_relative_to(root):
            raise ValueError("upload file moved outside the selected root")
        data = path.read_bytes()
        if len(data) != item["size"] or hashlib.sha256(data).hexdigest() != item["digest"]:
            raise ValueError("upload file changed after the manifest was collected")
        client._request(
            "PUT",
            f"/v1/uploads/{batch_id}/files",
            params={"relative_path": item["relative_path"]},
            content=data,
        )
    manifest_response = client._post(f"/v1/uploads/{batch_id}/complete")
    if kb_id is None:
        return manifest_response
    preview_request = {
        "kb_id": kb_id,
        "source_id": source_id,
        "selection": dict(selection or {}),
    }
    preview = client._post(f"/v1/kbs/{kb_id}/imports/preview", json=preview_request)
    applied = client._post(
        f"/v1/kbs/{kb_id}/imports",
        json={**preview_request, "expected_preview_hash": preview["preview_hash"]},
    )
    return {**preview, "job_id": applied.get("job_id"), "manifest": manifest_response}
