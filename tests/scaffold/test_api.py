"""API scaffold behaviour: honest 501s, 200 health, no business side effects."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

#: Every business route with a request the schema accepts must return 501.
BUSINESS_CASES: list[tuple[str, str, dict[str, object] | None]] = [
    ("POST", "/v1/kbs", {"name": "kb"}),
    ("GET", "/v1/kbs", None),
    ("GET", "/v1/kbs/kb1", None),
    ("PATCH", "/v1/kbs/kb1", {"name": "renamed"}),
    ("DELETE", "/v1/kbs/kb1", None),
    ("POST", "/v1/kbs/kb1/publish", {}),
    ("POST", "/v1/kbs/kb1/documents", {"kb_id": "kb1", "title": "t"}),
    ("GET", "/v1/kbs/kb1/documents", None),
    ("GET", "/v1/documents/doc1", None),
    ("PATCH", "/v1/documents/doc1", {"kb_id": "kb1", "title": "t"}),
    ("DELETE", "/v1/documents/doc1", None),
    ("POST", "/v1/kbs/kb1/qa-pairs", {"kb_id": "kb1", "question": "q", "answer": "a"}),
    ("GET", "/v1/kbs/kb1/qa-pairs", None),
    ("GET", "/v1/qa-pairs/qa1", None),
    ("PATCH", "/v1/qa-pairs/qa1", {"kb_id": "kb1", "question": "q", "answer": "a"}),
    ("DELETE", "/v1/qa-pairs/qa1", None),
    ("POST", "/v1/kbs/kb1/imports/preview", {"kb_id": "kb1", "source_id": "s1"}),
    ("POST", "/v1/kbs/kb1/imports", {
        "kb_id": "kb1", "source_id": "s1", "expected_preview_hash": "h",
    }),
    ("POST", "/v1/sources/s1/sync", {}),
    ("GET", "/v1/source-roots", None),
    ("POST", "/v1/source-roots/root1/scan", None),
    ("GET", "/v1/kbs/kb1/versions", None),
    ("GET", "/v1/versions/v1", None),
    ("GET", "/v1/kbs/kb1/version-diff?left=v1&right=v2", None),
    ("POST", "/v1/versions/v1/publish", {}),
    ("POST", "/v1/kbs/kb1/rollback", {"target_version_id": "v1"}),
    ("POST", "/v1/search", {"question": "q"}),
    ("POST", "/v1/ask", {"question": "q"}),
    ("POST", "/v1/sessions", {}),
    ("GET", "/v1/sessions/s1/history", None),
    ("POST", "/v1/sessions/s1/answers", {"question": "q"}),
    ("GET", "/v1/answers/a1", None),
    ("POST", "/v1/answers/a1/cancel", None),
    ("GET", "/v1/answers/a1/citations/c1", None),
    ("GET", "/v1/answers/a1/events", None),
    ("GET", "/v1/knowledge-catalog", None),
    ("POST", "/v1/knowledge-selection/preview", {"question": "q", "selection": {"mode": "auto"}}),
    ("GET", "/v1/sessions/s1/selection", None),
    ("PATCH", "/v1/sessions/s1/selection", {
        "selection": {"mode": "auto"},
        "expected_scope_revision": 0,
    }),
    ("POST", "/v1/answers/a1/feedback", {"rating": "like"}),
    ("GET", "/v1/issues", None),
    ("GET", "/v1/issues/i1", None),
    ("PATCH", "/v1/issues/i1", {}),
    ("POST", "/v1/issues/i1/retest", {}),
    ("POST", "/v1/models/discovery", {"target_ids": []}),
    ("GET", "/v1/models/runtimes", None),
    ("GET", "/v1/models", None),
    ("GET", "/v1/models/m1", None),
    ("GET", "/v1/inference-profiles", None),
    ("POST", "/v1/inference-profiles", {}),
    ("GET", "/v1/inference-profiles/p1", None),
    ("PUT", "/v1/inference-profiles/p1", {}),
    ("POST", "/v1/inference-profiles/p1/disable", {}),
    ("GET", "/v1/sessions/s1/inference", None),
    ("PATCH", "/v1/sessions/s1/inference", {
        "inference": {"policy": "local_only"},
        "expected_inference_revision": 0,
    }),
    ("POST", "/v1/model-installs/preview", {"target_id": "ollama", "model_ref": "x:1b"}),
    ("POST", "/v1/model-installs", {"preview_id": "p1", "preview_hash": "h", "confirmed": True}),
    ("POST", "/v1/models/m1/verifications", {"roles": ["generator"]}),
    ("GET", "/v1/jobs/j1", None),
    ("GET", "/v1/jobs/j1/events", None),
    ("POST", "/v1/jobs/j1/cancel", None),
    ("POST", "/v1/uploads", {"source_id": "s1", "files": []}),
    ("POST", "/v1/uploads/b1/complete", None),
]


def test_health_reports_scaffold(client: TestClient) -> None:
    body = client.get("/healthz").json()
    assert body == {"status": "ok", "mode": "scaffold", "schema_version": 2}
    assert client.get("/healthz").status_code == 200


def test_readiness_is_false(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json()["ready"] is False


def test_capabilities_advertise_unimplemented(client: TestClient) -> None:
    body = client.get("/v1/capabilities").json()
    assert body["mode"] == "scaffold"
    # Scaffold mode opens no database, so A1 business features stay unimplemented.
    assert "knowledge" in body["unimplemented"]
    assert "models" in body["unimplemented"]
    assert body["selection_limits"]["max_selected_kbs"] >= 1


@pytest.mark.parametrize(("method", "path", "payload"), BUSINESS_CASES)
def test_business_routes_return_501(
    client: TestClient, method: str, path: str, payload: dict[str, object] | None
) -> None:
    headers = {}
    if path == "/v1/model-installs" or path.endswith("/verifications"):
        headers["Idempotency-Key"] = "scaffold-test-key"
    response = client.request(method, path, json=payload, headers=headers)
    assert response.status_code == 501, response.text
    body = response.json()
    assert body["error"]["code"] == "FEATURE_NOT_IMPLEMENTED"
    assert body["request_id"]


def test_invalid_payload_is_422(client: TestClient) -> None:
    response = client.post("/v1/ask", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_FAILED"
    assert body["error"]["details"][0]["field"] == "question"


def test_unknown_field_is_rejected(client: TestClient) -> None:
    response = client.post("/v1/kbs", json={"name": "kb", "unexpected": True})
    assert response.status_code == 422


def test_selection_union_and_nonempty_targets(client: TestClient) -> None:
    empty = client.post(
        "/v1/search",
        json={"question": "q", "selection": {"mode": "explicit", "targets": []}},
    )
    assert empty.status_code == 422

    duplicate = client.post(
        "/v1/search",
        json={
            "question": "q",
            "selection": {
                "mode": "explicit",
                "targets": [{"kb_id": "a"}, {"kb_id": "a", "version_id": "v"}],
            },
        },
    )
    assert duplicate.status_code == 422

    empty_candidates = client.post(
        "/v1/search",
        json={"question": "q", "selection": {"mode": "auto", "candidate_kb_ids": []}},
    )
    assert empty_candidates.status_code == 422

    unknown_mode = client.post(
        "/v1/search", json={"question": "q", "selection": {"mode": "guess"}}
    )
    assert unknown_mode.status_code == 422


def test_inference_policy_and_profile_schema(client: TestClient) -> None:
    bad_policy = client.post(
        "/v1/ask", json={"question": "q", "inference": {"policy": "cloud"}}
    )
    assert bad_policy.status_code == 422

    accepted = client.post(
        "/v1/ask",
        json={"question": "q", "inference": {"profile_id": "p1", "policy": "local_only"}},
    )
    assert accepted.status_code == 501


def test_discovery_rejects_client_url_or_path(client: TestClient) -> None:
    for payload in (
        {"target_ids": ["ollama"], "url": "http://example.invalid"},
        {"target_ids": ["ollama"], "path": "C:/models"},
        {"target_ids": ["ollama"], "credential": "secret"},
    ):
        response = client.post("/v1/models/discovery", json=payload)
        assert response.status_code == 422, payload


def test_model_capabilities_is_static_scaffold(client: TestClient) -> None:
    body = client.get("/v1/models/capabilities").json()
    assert body["mode"] == "scaffold"
    assert body["install_requires_confirmation"] is True
    assert body["runtimes"] == []


def test_model_routes_return_501_without_provider_calls(
    client: TestClient, forbid_network: None, tmp_path
) -> None:
    for method, path, payload in [
        ("POST", "/v1/models/discovery", {"target_ids": ["ollama"]}),
        ("GET", "/v1/models", None),
        ("POST", "/v1/model-installs/preview", {"target_id": "ollama", "model_ref": "x"}),
    ]:
        assert client.request(method, path, json=payload).status_code == 501
    assert not (tmp_path / "var").exists()


def test_content_create_rejects_path_body_kb_mismatch(client: TestClient) -> None:
    for kind, body in (
        ("documents", {"kb_id": "different", "title": "t"}),
        ("qa-pairs", {"kb_id": "different", "question": "q", "answer": "a"}),
    ):
        response = client.post(f"/v1/kbs/current/{kind}", json=body)
        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "VALIDATION_FAILED"
    assert client.post(
        "/v1/kbs/current/documents", json={"kb_id": "current", "title": "t"}
    ).status_code == 501


def test_install_confirmation_requires_preview_and_idempotency(client: TestClient) -> None:
    missing = client.post("/v1/model-installs", json={"preview_hash": "h", "confirmed": True})
    assert missing.status_code == 422
    for body in (
        {"preview_id": "p1", "preview_hash": "h"},
        {"preview_id": "p1", "preview_hash": "h", "confirmed": False},
    ):
        response = client.post(
            "/v1/model-installs", json=body, headers={"Idempotency-Key": "key-1"}
        )
        assert response.status_code == 422, response.text

    well_formed = client.post(
        "/v1/model-installs",
        json={"preview_id": "p1", "preview_hash": "h", "confirmed": True},
        headers={"Idempotency-Key": "key-1"},
    )
    assert well_formed.status_code == 501


@pytest.mark.parametrize(
    ("path", "body"),
    [
        ("/v1/model-installs", {"preview_id": "p1", "preview_hash": "h", "confirmed": True}),
        ("/v1/models/m1/verifications", {"roles": ["generator"]}),
    ],
)
def test_model_jobs_require_nonempty_idempotency_key(
    client: TestClient, path: str, body: dict[str, object]
) -> None:
    for headers in ({}, {"Idempotency-Key": " "}):
        response = client.post(path, json=body, headers=headers)
        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "VALIDATION_FAILED"
    assert client.post(path, json=body, headers={"Idempotency-Key": "k1"}).status_code == 501


def test_model_jobs_advertise_idempotency_key_in_openapi(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    for path in ("/v1/model-installs", "/v1/models/{model_id}/verifications"):
        params = paths[path]["post"]["parameters"]
        assert any(
            p["name"] == "Idempotency-Key" and p["in"] == "header" and p["required"]
            for p in params
        )


def test_cross_origin_sse_resume_preflight_allows_cursor(tmp_path) -> None:
    from qa_service.app import create_app
    from qa_service.settings import Settings

    app = create_app(Settings(data_dir=tmp_path / "var", allowed_origins=["https://host.test"]))
    with TestClient(app, raise_server_exceptions=False) as cross_origin:
        response = cross_origin.options(
            "/v1/answers/a1/events",
            headers={
                "Origin": "https://host.test",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,last-event-id",
            },
        )
    assert response.status_code == 200, response.text
    assert response.headers["access-control-allow-origin"] == "https://host.test"
    assert "last-event-id" in response.headers["access-control-allow-headers"].lower()
    assert not (tmp_path / "var").exists()


def test_sse_preflight_returns_501(client: TestClient) -> None:
    response = client.get(
        "/v1/answers/a1/events", headers={"Accept": "text/event-stream"}
    )
    assert response.status_code == 501
    assert response.headers["content-type"].startswith("application/json")


def test_openapi_and_event_schema_export(client: TestClient, tmp_path) -> None:
    from scripts.export_contracts import build_event_schema

    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    assert "/v1/ask" in paths
    assert "/v1/models/discovery" in paths
    routes = {(method, path) for path, ops in paths.items() for method in ops}
    assert ("post", "/v1/knowledge-selection/preview") in routes
    assert ("patch", "/v1/sessions/{session_id}/selection") in routes

    discovery_schema = schema["components"]["schemas"]["DiscoveryRequest"]
    assert set(discovery_schema["properties"]) == {"target_ids"}
    assert discovery_schema["additionalProperties"] is False

    events = build_event_schema()
    assert events["answer_events"]["single_terminal"] is True
    assert events["error_codes"]["FEATURE_NOT_IMPLEMENTED"] == 501
    assert "answer_id" in events["answer_event"]["properties"]
    assert "job_id" in events["job_event"]["properties"]


def test_request_id_echoed(client: TestClient) -> None:
    response = client.get("/healthz", headers={"X-Request-ID": "abc123"})
    assert response.headers["X-Request-ID"] == "abc123"

    generated = client.post("/v1/ask", json={"question": "q"})
    assert generated.headers["X-Request-ID"]
    assert generated.json()["request_id"] == generated.headers["X-Request-ID"]
