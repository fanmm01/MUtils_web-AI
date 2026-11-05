"""``qa-api`` entry point. P1 binds loopback only and is not a production server."""

from __future__ import annotations

import argparse

from .app import create_app
from .settings import load_settings


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="qa-api", description="Q&A assistant scaffold API")
    parser.add_argument("--host", default=None, help="bind address (default: settings)")
    parser.add_argument("--port", type=int, default=None, help="bind port (default: settings)")
    parser.add_argument("--reload", action="store_true", help="development auto-reload")
    args = parser.parse_args(argv)

    settings = load_settings()
    host = args.host or settings.host
    port = args.port or settings.port
    if host not in {"127.0.0.1", "localhost", "::1"}:
        parser.error("the scaffold build binds loopback only; use a reverse proxy in later phases")

    import uvicorn

    uvicorn.run(create_app(settings), host=host, port=port, reload=args.reload)


if __name__ == "__main__":
    main()
