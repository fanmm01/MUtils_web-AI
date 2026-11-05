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
    root = root.resolve()
    wanted = set(relative_paths) if relative_paths is not None else None
    manifest: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if wanted is not None and relative not in wanted:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest.append(
            {"relative_path": relative, "digest": digest, "size": path.stat().st_size}
        )
    return manifest


def upload_directory(
    client: Client, root: Path, selection: Mapping[str, object] | None = None
) -> dict[str, object]:
    """Begin a batch, stream each file, then complete it. Returns the manifest."""
    manifest = collect_upload(root, None)
    batch = client._post("/v1/uploads", json={"files": manifest, "selection": selection})
    batch_id = batch.get("batch_id") if isinstance(batch, dict) else None
    if not batch_id:
        raise RuntimeError("upload batch was not accepted")
    for item in manifest:
        path = root / str(item["relative_path"])
        client._http.put(
            f"/v1/uploads/{batch_id}/files",
            params={"relative_path": item["relative_path"]},
            content=path.read_bytes(),
        )
    return client._post(f"/v1/uploads/{batch_id}/complete")
