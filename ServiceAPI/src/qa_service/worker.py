"""Background worker entry point.

P1 keeps the entry point and dispatch table only. No job kind executes: the
worker must refuse to start processing rather than consume a queue it cannot
serve honestly.
"""

from __future__ import annotations

import argparse
import signal
import threading

from qa_contracts.operations import JobKind

from .container import Container
from .settings import load_settings

SUPPORTED_KINDS: tuple[JobKind, ...] = (
    JobKind.IMPORT,
    JobKind.MODEL_INSTALL,
    JobKind.MODEL_VERIFY,
)


def dispatch(job_kind: JobKind) -> None:
    """Route a claimed job. Unimplemented in P1; later phases fill this in."""
    raise NotImplementedError(f"job kind {job_kind.value} is not implemented in the scaffold")


def run_worker(container: Container, stop_signal: threading.Event) -> None:
    del container
    raise NotImplementedError("the scaffold build has no persistent job queue to consume")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="qa-worker", description="Q&A assistant worker")
    parser.add_argument(
        "--once", action="store_true", help="run a single poll cycle (unimplemented in P1)"
    )
    parser.parse_args(argv)
    settings = load_settings()
    stop = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    try:
        run_worker(Container(settings=settings), stop)
    except NotImplementedError as exc:
        raise SystemExit(f"qa-worker: {exc}") from exc


if __name__ == "__main__":
    main()
