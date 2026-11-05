"""The Python SDK maps transport errors and never re-implements business rules."""

from __future__ import annotations

import httpx
import pytest

from qa_client import Client, QAError
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
