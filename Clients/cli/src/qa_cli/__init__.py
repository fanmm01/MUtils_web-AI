"""CLI package.

The Typer application is re-exported; the console entry point in
``pyproject.toml`` targets ``qa_cli.main:main`` directly, so the module
attribute is not shadowed by a same-named function here.
"""

from __future__ import annotations

from .main import app

__all__ = ["app"]
