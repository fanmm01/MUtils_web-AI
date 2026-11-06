"""The Python SDK maps transport errors and never re-implements business rules."""

from __future__ import annotations

import hashlib

import httpx
import pytest

from qa_client import Client, QAError
from qa_client.files import collect_upload, upload_directory
from qa_client.sse import decode_sse, resume_cursor


def _client(handler) -> Client:
    return Client("http://127.0.0.1:8000", transport=httpx.MockTransport(handler))


def test_error_envelope_becomes_qa_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            501,
            json={
                "error": {
                    "code": "FEATURE_NOT_IMPLEMENTED",
                    "message": "not yet",
                    "details": [{"field": "question", "reason": "missing"}],
                },
                "request_id": "req-9",
            },
            headers={"X-Request-ID": "req-9"},
        )

    with pytest.raises(QAError) as excinfo:
        _client(handler).search("q")
    error = excinfo.value
    assert error.code == "FEATURE_NOT_IMPLEMENTED"
    assert error.status == 501
    assert error.request_id == "req-9"
    assert error.details[0].field == "question"


def test_unrecognized_error_payload_is_safe() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="<html>boom</html>")

    with pytest.raises(QAError) as excinfo:
        _client(handler).health()
    assert excinfo.value.code == "INTERNAL_ERROR"
    assert "boom" not in str(excinfo.value)


def test_install_preview_then_confirm_only() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(f"{request.method} {request.url.path}")
        return httpx.Response(501, json={"error": {"code": "FEATURE_NOT_IMPLEMENTED",
                                                   "message": "no", "details": []},
                                         "request_id": "r"})

    client = _client(handler)
    with pytest.raises(QAError):
        client.preview_install({"target_id": "ollama", "model_ref": "qwen3:8b"})
    with pytest.raises(QAError):
        client.confirm_install(
            {"preview_id": "p1", "preview_hash": "h", "confirmed": True},
            idempotency_key="key",
        )
    assert seen == ["POST /v1/model-installs/preview", "POST /v1/model-installs"]
    assert not hasattr(client, "pull_model")
    assert not hasattr(client, "start_download")


def test_model_job_clients_send_required_idempotency_header() -> None:
    seen: list[tuple[str, str | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.path, request.headers.get("Idempotency-Key")))
        return httpx.Response(501, json={
            "error": {"code": "FEATURE_NOT_IMPLEMENTED", "message": "not yet", "details": []},
            "request_id": "r",
        })

    client = _client(handler)
    for call in (
        lambda: client.confirm_install(
            {"preview_id": "p1", "preview_hash": "h", "confirmed": True}, "install-1"
        ),
        lambda: client.verify_model("model-1", {"roles": ["generator"]}, "verify-1"),
    ):
        with pytest.raises(QAError):
            call()
    assert seen == [
        ("/v1/model-installs", "install-1"),
        ("/v1/models/model-1/verifications", "verify-1"),
    ]
    with pytest.raises(ValueError, match="required"):
        client.verify_model("model-1", {"roles": ["generator"]}, " ")
    assert len(seen) == 2


def test_python_conflict_resolver_sends_required_idempotency_key() -> None:
    seen: list[tuple[str, str | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.path, request.headers.get("Idempotency-Key")))
        return httpx.Response(501, json={
            "error": {"code": "FEATURE_NOT_IMPLEMENTED", "message": "not yet", "details": []},
            "request_id": "r",
        })

    client = _client(handler)
    with pytest.raises(ValueError, match="required"):
        client.resolve_import_conflicts("kb1", "preview1", {}, " ")
    with pytest.raises(QAError):
        client.resolve_import_conflicts("kb1", "preview1", {}, "resolve-1")
    assert seen == [
        ("/v1/kbs/kb1/imports/preview1/resolve", "resolve-1"),
    ]


def test_job_json_cursor_uses_replay_header_and_rejects_json_as_sse() -> None:
    seen: list[tuple[str | None, str | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.headers.get("Last-Event-ID"), request.headers.get("Accept")))
        return httpx.Response(200, json=[])

    client = _client(handler)
    assert list(client.job_events("j1", 4)) == []
    with pytest.raises(QAError, match="expected text/event-stream job events"):
        list(client.subscribe_job("j1", 4))
    assert seen == [("4", "application/json"), ("4", "text/event-stream")]


def test_upload_rejects_symlinks_before_any_network_request(tmp_path) -> None:
    root = tmp_path / "upload"
    root.mkdir()
    outside = tmp_path / "private.txt"
    outside.write_text("outside root", encoding="utf-8")
    try:
        (root / "link.txt").symlink_to(outside)
    except (NotImplementedError, OSError):
        pytest.skip("creating file symlinks requires unavailable privileges")

    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail(f"unexpected upload request: {request.method} {request.url}")

    with pytest.raises(ValueError, match="symlinks"):
        upload_directory(_client(handler), root, source_id="source-1")


def test_upload_rejects_symlink_even_without_link_privileges(tmp_path, monkeypatch) -> None:
    root = tmp_path / "upload"
    root.mkdir()
    (root / "doc.md").write_text("document", encoding="utf-8")
    original_is_symlink = type(root).is_symlink

    def marked_symlink(path):
        return path.name == "doc.md" or original_is_symlink(path)

    monkeypatch.setattr(type(root), "is_symlink", marked_symlink)
    with pytest.raises(ValueError, match="symlinks"):
        collect_upload(root)


def test_upload_posts_manifest_and_stops_after_failed_file_put(tmp_path) -> None:
    root = tmp_path / "upload"
    root.mkdir()
    (root / "doc.md").write_text("document", encoding="utf-8")
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(f"{request.method} {request.url.path}")
        if request.url.path == "/v1/uploads":
            body = request.content.decode("utf-8")
            import json

            manifest = json.loads(body)
            assert set(manifest) == {"source_id", "selection", "files"}
            assert manifest["selection"] == {}
            assert manifest["source_id"] == "source-1"
            assert manifest["files"] == [{
                "relative_path": "doc.md",
                "digest": hashlib.sha256(b"document").hexdigest(),
                "size": 8,
            }]
            return httpx.Response(202, json={"batch_id": "batch-1"})
        assert request.url.params["relative_path"] == "doc.md"
        assert request.content == b"document"
        return httpx.Response(501, json={
            "error": {"code": "FEATURE_NOT_IMPLEMENTED", "message": "not yet", "details": []},
            "request_id": "req-1",
        })

    with pytest.raises(QAError, match="not yet"):
        upload_directory(_client(handler), root, source_id="source-1")
    assert calls == ["POST /v1/uploads", "PUT /v1/uploads/batch-1/files"]


def test_upload_rejects_missing_requested_files(tmp_path) -> None:
    root = tmp_path / "upload"
    root.mkdir()
    (root / "doc.md").write_text("document", encoding="utf-8")
    with pytest.raises(ValueError, match="not found"):
        collect_upload(root, ["missing.txt"])


def test_sse_handles_utf8_split_and_heartbeat() -> None:
    payload = (
        'id: 1\nevent: answer.delta\ndata: {"text":"你好"}\n\n'
        ": heartbeat\n\n"
        'id: 2\nevent: answer.completed\ndata: {"text":"好"}\n\n'
    ).encode()
    # Split inside a multi-byte character and inside a line, one byte per chunk.
    chunks = [payload[i : i + 1] for i in range(len(payload))]
    events = list(decode_sse(chunks))
    assert [event.id for event in events] == [1, 2]
    assert events[0].json()["text"] == "你好"
    assert events[1].event == "answer.completed"
    assert resume_cursor(events) == 2


def test_sse_multiline_data_joined() -> None:
    raw = b'data: {"a":\ndata: 1}\n\n'
    events = list(decode_sse([raw]))
    assert events[0].data == '{"a":\n1}'
