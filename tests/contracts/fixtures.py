"""Provider/consumer fixtures shared by both backend streams.

They describe the wire shape only. A1 implements providers (storage, API), A2
implements consumers (core semantics); either side can run against these
fixtures without the other's code.
"""

from __future__ import annotations

import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict[str, object]:
    path = FIXTURE_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def available_fixtures() -> list[str]:
    return sorted(path.name for path in FIXTURE_DIR.glob("*.json"))


REQUEST_FIXTURES = (
    "search_explicit_single.json",
    "ask_auto_candidates.json",
    "session_selection_update.json",
    "discovery_allowlisted.json",
    "install_confirmation.json",
)

FORBIDDEN_DISCOVERY_FIXTURES = (
    "discovery_with_url.json",
    "discovery_with_path.json",
)
