"""Development helpers: start/stop the API, worker and examples.

Each component is started by this script and stopped by it; nothing is left
running. The API binds loopback in P1.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class ProcessHandle:
    name: str
    process: subprocess.Popen[bytes]
    log_path: Path = field(default=Path(""))


COMPONENTS: dict[str, list[str]] = {
    "api": [sys.executable, "-m", "qa_service", "--host", "127.0.0.1"],
    "worker": [sys.executable, "-m", "qa_service.worker", "--once"],
}


def start(
    component: str, settings: Mapping[str, str] | None = None, extra: list[str] | None = None
) -> ProcessHandle:
    """Start one component; ``settings`` are extra CLI flags, not credentials."""
    if component not in COMPONENTS:
        raise SystemExit(f"unknown component '{component}'; choose from {sorted(COMPONENTS)}")
    overrides = [item for key, value in (settings or {}).items() for item in (key, value)]
    command = [*COMPONENTS[component], *overrides, *(extra or [])]
    process = subprocess.Popen(command, cwd=ROOT)
    return ProcessHandle(name=component, process=process)


def stop(handles: list[ProcessHandle]) -> None:
    for handle in reversed(handles):
        if handle.process.poll() is None:
            handle.process.terminate()
            try:
                handle.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                handle.process.kill()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run scaffold components")
    parser.add_argument("component", nargs="?", default="api", choices=sorted(COMPONENTS))
    parser.add_argument("extra", nargs=argparse.REMAINDER, help="arguments passed through")
    args = parser.parse_args(argv)
    handle = start(args.component, None, args.extra)
    try:
        return handle.process.wait()
    except KeyboardInterrupt:
        return 130
    finally:
        stop([handle])


if __name__ == "__main__":
    raise SystemExit(main())
