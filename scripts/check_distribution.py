"""Verify no model weights are tracked or packaged.

Heuristics only: extension, relative path and size checks catch the common
mistakes but are not a licence review and cannot prove a distribution is
weight-free.
"""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WEIGHT_SUFFIXES = {
    ".gguf",
    ".ggml",
    ".safetensors",
    ".bin",
    ".pt",
    ".pth",
    ".onnx",
    ".ckpt",
    ".h5",
}
WEIGHT_DIRS = {".ollama", "models", "model_cache", "blobs"}
LARGE_FILE_BYTES = 50 * 1024 * 1024
#: Never recurse into these; they hold installed dependencies, not deliverables.
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache"}


@dataclass
class DistributionReport:
    checked: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


def _is_weight(path: Path, size: int) -> str | None:
    if path.suffix.lower() in WEIGHT_SUFFIXES:
        return f"weight file: {path}"
    if {part.lower() for part in path.parts} & WEIGHT_DIRS and size > LARGE_FILE_BYTES:
        return f"large file in a model directory: {path}"
    return None


def scan_artifacts(paths: list[Path]) -> DistributionReport:
    """Check explicit files and recurse into directories.

    Relative paths are taken from the repository root so a directory that is
    merely *named* like a model cache in a parent path does not raise a false
    positive.
    """
    report = DistributionReport()
    for entry in paths:
        try:
            relative = entry.resolve().relative_to(ROOT)
        except ValueError:
            relative = entry
        report.checked.append(str(relative))
        candidates = [entry] if entry.is_file() else (
            [
                path
                for path in entry.rglob("*")
                if path.is_file()
                and not (set(path.relative_to(entry).parts) & SKIP_DIRS)
            ]
            if entry.is_dir()
            else []
        )
        for path in candidates:
            finding = _is_weight(relative / path.relative_to(entry), path.stat().st_size)
            if finding:
                report.problems.append(finding)
    return report


def assert_no_model_weights(report: DistributionReport) -> None:
    if report.problems:
        raise SystemExit("model weights found:\n" + "\n".join(report.problems))


def tracked_git_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=False
    )
    if result.returncode != 0:
        return []
    names = result.stdout.decode("utf-8", errors="surrogateescape").split("\0")
    return [ROOT / name for name in names if name]


SOURCE_ROOTS = (
    "Contracts",
    "Q&A_Assistant",
    "KBManagement",
    "Infrastructure",
    "ServiceAPI",
    "Clients",
    "docs",
    "scripts",
    "tests",
)


def default_targets() -> list[Path]:
    """Tracked files, source trees and distribution folders that exist.

    Source trees are scanned even before they are committed, so a prepared
    build cannot hide weights merely by being new.
    """
    targets = tracked_git_files()
    for name in (*SOURCE_ROOTS, "dist", "build", "container", "docker", "Clients/desktop-go/dist"):
        candidate = ROOT / name
        if candidate.exists():
            targets.append(candidate)
    return list(dict.fromkeys(targets))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check distributions exclude model weights")
    parser.add_argument("paths", nargs="*", type=Path, help="files/directories to scan")
    parser.add_argument("--check", action="store_true", help="exit non-zero on findings")
    args = parser.parse_args(argv)

    report = scan_artifacts(args.paths or default_targets())
    print(f"checked {len(report.checked)} path(s); {len(report.problems)} problem(s)")
    for problem in report.problems:
        print(problem)
    if args.check:
        assert_no_model_weights(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
