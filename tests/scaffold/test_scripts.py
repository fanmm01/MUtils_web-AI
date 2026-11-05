"""Engineering scripts must be read-only and honest about what they inspect."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.check_distribution import (
    DistributionReport,
    assert_no_model_weights,
    scan_artifacts,
)
from scripts.check_environment import (
    inspect_model_runtime_candidates,
    inspect_optional_tools,
    inspect_runtime,
)


def test_environment_report_is_read_only(forbid_network: None) -> None:
    """``forbid_network`` turns any socket connect into a failure."""
    report = inspect_runtime()
    assert report.python.startswith("3.")
    assert report.root
    assert report.capabilities.tools
    assert inspect_optional_tools().note.startswith("PATH check only")


def test_runtime_hint_never_probes() -> None:
    hint = inspect_model_runtime_candidates({"runtime_targets": "ollama,lmstudio"})
    assert hint.configured_targets == ["ollama", "lmstudio"]
    assert hint.probed is False
    assert "authorized API action" in hint.note


def test_distribution_flags_weight_files(tmp_path: Path) -> None:
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "model.gguf").write_bytes(b"weights")
    report = scan_artifacts([tmp_path])
    assert any("model.gguf" in problem for problem in report.problems)


def test_distribution_ignores_dependency_directories(tmp_path: Path) -> None:
    node_modules = tmp_path / "node_modules" / "pkg"
    node_modules.mkdir(parents=True)
    (node_modules / "blob.bin").write_bytes(b"x")
    report = scan_artifacts([tmp_path])
    assert report.problems == []


def test_assert_no_model_weights_exits_on_findings(tmp_path: Path) -> None:
    try:
        assert_no_model_weights(DistributionReport(problems=["weight file: x.gguf"]))
    except SystemExit as exc:
        assert "x.gguf" in str(exc)
    else:  # pragma: no cover - the assertion above is the point
        raise AssertionError("expected SystemExit")


def test_events_artifact_is_truthful_about_terminal_states() -> None:
    from scripts.export_contracts import build_event_schema

    schema = build_event_schema()
    assert schema["answer_events"]["terminal"] == [
        "answer.completed",
        "answer.refused",
        "answer.failed",
        "answer.cancelled",
    ]
    assert json.dumps(schema)  # serialisable without a live app
