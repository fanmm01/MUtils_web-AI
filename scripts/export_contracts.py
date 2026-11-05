"""Export and verify the frozen contracts.

``--check`` fails when a generated artifact is stale, so a Contract Gate change
cannot land without regenerating the schema clients consume. No database,
network or model call happens here.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from qa_contracts.answers import AnswerEvent
from qa_contracts.errors import STATUS_BY_CODE, ErrorCode
from qa_contracts.operations import JobEvent

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OPENAPI_PATH = DOCS / "openapi.json"
EVENTS_PATH = DOCS / "events.schema.json"


def export_openapi(app, path: Path) -> dict[str, object]:
    schema = app.openapi()
    path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return schema


def build_event_schema() -> dict[str, object]:
    """SSE contract: answer and job events are separate shapes with stable IDs."""
    return {
        "schema_version": 1,
        "answer_event": AnswerEvent.model_json_schema(),
        "job_event": JobEvent.model_json_schema(),
        "event_types": {
            "answer": [
                "answer.accepted",
                "inference.bound",
                "selection.resolved",
                "retrieval.completed",
                "citation.ready",
                "answer.delta",
                "answer.completed",
                "answer.refused",
                "answer.failed",
                "answer.cancelled",
            ],
            "job": [
                "job.accepted",
                "job.progress",
                "job.completed",
                "job.failed",
                "job.cancelled",
            ],
        },
        "error_codes": {
            code.value: STATUS_BY_CODE[code] for code in ErrorCode
        },
        "answer_events": {
            "terminal": [
                "answer.completed",
                "answer.refused",
                "answer.failed",
                "answer.cancelled",
            ],
            "single_terminal": True,
            "ids": "answer_id and session_id on every event",
            "replay": "Last-Event-ID maps to seq; duplicates are dropped by the client",
        },
        "job_events": {
            "ids": "job_id on every event; never fabricates an answer_id",
            "bytes_unknown": "total_bytes may be null; no percentage is invented",
        },
    }


def export_events(path: Path) -> dict[str, object]:
    schema = build_event_schema()
    path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return schema


def check_contracts() -> list[str]:
    """Return a list of staleness problems; empty means contracts match code."""
    problems: list[str] = []
    from qa_service.app import create_app

    expected_openapi = json.loads(json.dumps(create_app().openapi(), sort_keys=True))
    if not OPENAPI_PATH.exists():
        problems.append(f"missing {OPENAPI_PATH.relative_to(ROOT)}")
    else:
        actual = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))
        if actual != expected_openapi:
            problems.append(
                f"{OPENAPI_PATH.relative_to(ROOT)} is stale; run scripts/export_contracts.py"
            )
    if not EVENTS_PATH.exists():
        problems.append(f"missing {EVENTS_PATH.relative_to(ROOT)}")
    else:
        actual_events = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
        if actual_events != build_event_schema():
            problems.append(
                f"{EVENTS_PATH.relative_to(ROOT)} is stale; run scripts/export_contracts.py"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export OpenAPI and SSE contract artifacts")
    parser.add_argument("--check", action="store_true", help="verify artifacts are up to date")
    args = parser.parse_args(argv)

    if args.check:
        problems = check_contracts()
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1 if problems else 0

    from qa_service.app import create_app

    DOCS.mkdir(parents=True, exist_ok=True)
    export_openapi(create_app(), OPENAPI_PATH)
    export_events(EVENTS_PATH)
    print(f"wrote {OPENAPI_PATH.relative_to(ROOT)} and {EVENTS_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
