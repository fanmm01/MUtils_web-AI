"""Provider/consumer fixtures shared by both backend streams.

They describe the wire shape only. A1 implements providers (storage, API), A2
implements consumers (core semantics); either side can run against these
fixtures without the other's code.
"""

from __future__ import annotations

import json
from pathlib import Path

from qa_contracts.base import HTTP_SCHEMA_VERSION

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict[str, object]:
    path = FIXTURE_DIR / name
    fixture = json.loads(path.read_text(encoding="utf-8"))
    if fixture["schema_version"] != HTTP_SCHEMA_VERSION:
        raise ValueError(f"{name} is not an HTTP v{HTTP_SCHEMA_VERSION} fixture")
    return fixture


def available_fixtures() -> list[str]:
    return sorted(path.name for path in FIXTURE_DIR.glob("*.json"))


REQUEST_FIXTURES = (
    "search_explicit_single.json",
    "ask_auto_candidates.json",
    "session_selection_update.json",
    "discovery_allowlisted.json",
    "install_confirmation.json",
    "upload_manifest_partial.json",
    "import_preview_mirror.json",
    "import_confirm_mirror.json",
    "resolve_keep_manual.json",
    "resolve_use_source.json",
    "resolve_fork_document.json",
)

FORBIDDEN_DISCOVERY_FIXTURES = (
    "discovery_with_url.json",
    "discovery_with_path.json",
)
