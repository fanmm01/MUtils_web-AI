"""CLI scaffold: help, selection flags, install confirmation and exit codes."""

from __future__ import annotations

import json

import httpx
import pytest
import typer
from typer.testing import CliRunner

import qa_cli.main
from qa_cli.main import _selection, app, main

runner = CliRunner()


def _mock_client(monkeypatch: pytest.MonkeyPatch, status: int, payload: object) -> list[dict]:
    recorded: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append({"method": request.method, "url": str(request.url),
                         "headers": dict(request.headers), "body": request.content})
        return httpx.Response(status, json=payload, headers={"X-Request-ID": "req-cli"})

    transport = httpx.MockTransport(handler)
    real_client = qa_cli.main.Client

    def factory(base_url: str, credential: str | None = None, timeout: float = 30.0):
        return real_client(base_url, credential, timeout, transport=transport)

    monkeypatch.setattr(qa_cli.main, "Client", factory)
    return recorded


def test_help_lists_management_qa_and_model_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("search", "ask", "kb", "content", "models", "jobs"):
        assert command in result.output

    models_help = runner.invoke(app, ["models", "--help"])
    assert models_help.exit_code == 0
    for command in (
        "capabilities",
        "discover",
        "runtimes",
        "install-preview",
        "install-confirm",
        "verify",
    ):
        assert command in models_help.output


def test_install_has_no_bypass_confirmation_command() -> None:
    """There is no command that downloads a model without a preview reference."""
    result = runner.invoke(app, ["models", "--help"])
    assert "install-now" not in result.output
    assert "pull" not in result.output

    no_yes = runner.invoke(
        app,
        ["models", "install-confirm", "--preview-id", "p1", "--preview-hash", "h",
         "--idempotency-key", "install-1"],
    )
    assert no_yes.exit_code != 0
    assert "--yes" in no_yes.output or "requires" in no_yes.output


def test_unimplemented_command_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _mock_client(
        monkeypatch,
        501,
        {
            "error": {
                "code": "FEATURE_NOT_IMPLEMENTED",
                "message": "not yet",
                "details": [],
            },
            "request_id": "req-cli",
        },
    )
    with pytest.raises(SystemExit) as excinfo:
        main(["--json", "search", "hello"])
    assert excinfo.value.code == 3
    captured = capsys.readouterr()
    assert "FEATURE_NOT_IMPLEMENTED" in captured.err


def test_json_error_is_machine_readable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _mock_client(
        monkeypatch,
        501,
        {
            "error": {
                "code": "FEATURE_NOT_IMPLEMENTED",
                "message": "not yet",
                "details": [],
            },
            "request_id": "req-cli",
        },
    )
    with pytest.raises(SystemExit):
        main(["--json", "ask", "hello"])
    payload = json.loads(capsys.readouterr().err.strip().splitlines()[-1])
    assert payload["code"] == "FEATURE_NOT_IMPLEMENTED"
    assert payload["request_id"] == "req-cli"
    assert payload["message"] == "not yet"


def test_model_job_commands_require_and_forward_idempotency_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded = _mock_client(monkeypatch, 501, {
        "error": {"code": "FEATURE_NOT_IMPLEMENTED", "message": "not yet", "details": []},
        "request_id": "req-cli",
    })
    for args in (
        ["models", "install-confirm", "--preview-id", "p1", "--preview-hash", "h", "--yes"],
        ["models", "verify", "model-1", "--role", "generator"],
    ):
        result = runner.invoke(app, args)
        assert result.exit_code != 0
        assert "--idempotency-key" in result.output
    assert recorded == []
    for args, expected in (
        (["models", "install-confirm", "--preview-id", "p1", "--preview-hash", "h",
          "--yes", "--idempotency-key", "install-1"], "install-1"),
        (["models", "verify", "model-1", "--role", "generator",
          "--idempotency-key", "verify-1"], "verify-1"),
    ):
        result = runner.invoke(app, args)
        assert result.exit_code != 0  # scaffold business endpoint returns 501
        assert recorded[-1]["headers"]["idempotency-key"] == expected


def test_selection_flags_translate_to_one_union() -> None:
    single = _selection(["kb_product"], False, None, None)
    assert single == {"mode": "explicit", "targets": [{"kb_id": "kb_product"}]}

    versioned = _selection(["kb_product@v3", "kb_ops"], False, None, None)
    assert versioned == {
        "mode": "explicit",
        "targets": [
            {"kb_id": "kb_product", "version_id": "v3"},
            {"kb_id": "kb_ops"},
        ],
    }

    auto = _selection(None, True, ["kb_a", "kb_b"], 2)
    assert auto == {"mode": "auto", "candidate_kb_ids": ["kb_a", "kb_b"], "max_kbs": 2}

    with pytest.raises(typer.BadParameter):
        _selection(["kb_a"], True, None, None)


def test_search_sends_selection_and_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded = _mock_client(monkeypatch, 501, {"error": {"code": "FEATURE_NOT_IMPLEMENTED",
                                                         "message": "no", "details": []},
                                               "request_id": "r"})
    runner.invoke(
        app,
        ["ask", "upgrade?", "--kb", "kb_product@v3", "--kb", "kb_ops",
         "--inference-profile", "local", "--inference-policy", "local_only",
         "--idempotency-key", "key-1"],
    )
    body = json.loads(recorded[-1]["body"])
    assert body["selection"]["mode"] == "explicit"
    assert body["selection"]["targets"][1] == {"kb_id": "kb_ops"}
    assert body["inference"] == {"profile_id": "local", "policy": "local_only"}
    assert recorded[-1]["headers"]["idempotency-key"] == "key-1"
