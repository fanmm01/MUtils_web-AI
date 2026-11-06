"""Explicit migration entry point (``qa-migrate``).

Applications never migrate on start-up or import. An operator runs this once
against a data directory, then starts ``qa-api``/``qa-worker``.
"""

from __future__ import annotations

import argparse
import asyncio

from .container import build_container
from .settings import load_settings


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="qa-migrate", description="apply schema migrations")
    parser.add_argument("--target", default="head", help="migration version or 'head'")
    parser.add_argument("--data-dir", default=None, help="override QA_DATA_DIR")
    args = parser.parse_args(argv)
    settings = load_settings()
    if args.data_dir:
        from pathlib import Path

        settings = settings.model_copy(update={"data_dir": Path(args.data_dir)})
    container = build_container(settings)
    if container.store is None:
        parser.error("the container could not be built")
    result = asyncio.run(container.store.migrate(args.target))
    print(
        f"schema version {result.version}; applied {len(result.applied)},"
        f" skipped {len(result.skipped)}"
    )
    for name in result.applied:
        print(f"applied {name}")


if __name__ == "__main__":
    main()
