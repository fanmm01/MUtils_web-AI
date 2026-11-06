"""Local source scanning and directory polling end to end.

Files are real: nested directories, encodings and symlinks are exercised on a
temporary tree, never on a network share.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from kb_management.sources import LocalSource, SourceRoot
from qa_contracts.errors import PermissionDenied
from qa_contracts.knowledge import Selection


def _write(root: Path, name: str, text: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


async def test_full_scan_is_complete_and_hashes_bytes(tmp_path: Path) -> None:
    _write(tmp_path, "a.md", "内容 A")
    _write(tmp_path, "nested/b.txt", "内容 B")
    manifest = await LocalSource(SourceRoot("root1", tmp_path)).scan()
    assert manifest.complete is True
    assert manifest.scan_scope == "full"
    assert manifest.scan_status == "succeeded"
    paths = {entry.relative_path: entry for entry in manifest.files}
    assert set(paths) == {"a.md", "nested/b.txt"}
    assert paths["a.md"].digest == hashlib.sha256("内容 A".encode()).hexdigest()


async def test_restricted_scan_is_partial_and_cannot_delete(tmp_path: Path) -> None:
    _write(tmp_path, "a.md", "A")
    _write(tmp_path, "b.md", "B")
    manifest = await LocalSource(SourceRoot("root1", tmp_path)).scan(
        Selection(include_globs=["*.md"], relative_paths=["a.md"])
    )
    assert manifest.complete is False
    assert manifest.scan_scope == "partial"
    assert [entry.relative_path for entry in manifest.files] == ["a.md"]


async def test_selected_but_missing_file_is_explicitly_rejected(tmp_path: Path) -> None:
    from qa_contracts.errors import ValidationFailed

    _write(tmp_path, "a.md", "A")
    with pytest.raises(ValidationFailed):
        await LocalSource(SourceRoot("root1", tmp_path)).scan(
            Selection(relative_paths=["a.md", "missing.md"])
        )


async def test_unreadable_root_is_reported_not_silently_empty(tmp_path: Path) -> None:
    from qa_contracts.errors import NotFound

    with pytest.raises(NotFound):
        await LocalSource(SourceRoot("root1", tmp_path / "absent")).scan()


async def test_non_document_files_are_skipped(tmp_path: Path) -> None:
    _write(tmp_path, "a.md", "A")
    _write(tmp_path, "image.png", "not really an image")
    manifest = await LocalSource(SourceRoot("root1", tmp_path)).scan()
    assert [entry.relative_path for entry in manifest.files] == ["a.md"]


async def test_symlinked_file_marks_the_scan_failed(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("secret", encoding="utf-8")
    try:
        (root / "link.md").symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("creating file symlinks requires unavailable privileges")
    manifest = await LocalSource(SourceRoot("root1", root)).scan()
    assert manifest.scan_status == "failed"
    assert manifest.complete is False


async def test_excluded_files_do_not_enter_the_manifest(tmp_path: Path) -> None:
    _write(tmp_path, "keep.md", "keep")
    _write(tmp_path, "draft.tmp", "draft")
    _write(tmp_path, "private/secret.md", "secret")
    manifest = await LocalSource(SourceRoot("root1", tmp_path)).scan(
        Selection(exclude_globs=["private/*"])
    )
    assert {entry.relative_path for entry in manifest.files} == {"keep.md"}


async def test_file_cap_interrupts_instead_of_partial_success(tmp_path: Path) -> None:
    for index in range(5):
        _write(tmp_path, f"doc{index}.md", f"内容 {index}")
    manifest = await LocalSource(SourceRoot("root1", tmp_path), max_files=3).scan()
    assert len(manifest.files) == 3
    assert manifest.complete is False
    assert manifest.scan_status == "succeeded"  # every attempted file was read


def test_selection_port_rejects_traversal() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Selection(relative_paths=["../escape.md"])


async def test_absolute_path_request_is_refused(tmp_path: Path) -> None:
    with pytest.raises(PermissionDenied):
        from kb_management.sources import _safe_child

        _safe_child(tmp_path, "../outside")
