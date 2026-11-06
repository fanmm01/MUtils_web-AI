"""Provider contract tests (run by A1): the API honours the frozen fixtures.

Uses only the real scaffold app plus the shared fixtures; no A2 imports.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.contracts.fixtures import (
    FORBIDDEN_DISCOVERY_FIXTURES,
    REQUEST_FIXTURES,
    load_fixture,
)


@pytest.mark.parametrize("fixture_name", REQUEST_FIXTURES)
def test_valid_fixture_is_accepted_by_schema(
    client: TestClient, fixture_name: str
) -> None:
    fixture = load_fixture(fixture_name)
    response = client.request(
        str(fixture["method"]),
        str(fixture["path"]),
        json=fixture["body"],
        headers=fixture.get("headers", {}),
    )
    assert response.status_code == 501, (
        f"{fixture_name} should pass validation then report 501; got "
        f"{response.status_code}: {response.text}"
    )
    assert response.json()["error"]["code"] == "FEATURE_NOT_IMPLEMENTED"


@pytest.mark.parametrize("fixture_name", FORBIDDEN_DISCOVERY_FIXTURES)
def test_discovery_fixture_with_endpoint_is_rejected(
    client: TestClient, fixture_name: str
) -> None:
    fixture = load_fixture(fixture_name)
    response = client.request(
        str(fixture["method"]), str(fixture["path"]), json=fixture["body"]
    )
    assert response.status_code == fixture["expect_status"]
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_p2_gate_rejects_unconfirmed_mirror_and_client_complete(client: TestClient) -> None:
    unconfirmed = client.post(
        "/v1/kbs/kb1/imports", json={"kb_id": "kb1", "source_id": "source_1", "mode": "mirror"}
    )
    assert unconfirmed.status_code == 422
    assert unconfirmed.json()["error"]["code"] == "VALIDATION_FAILED"
    untrusted = client.post(
        "/v1/uploads", json={"source_id": "source_1", "complete": True, "files": []}
    )
    assert untrusted.status_code == 422
    assert untrusted.json()["error"]["code"] == "VALIDATION_FAILED"


@pytest.mark.parametrize("suffix", ("imports/preview", "imports"))
def test_import_routes_reject_conflicting_kb_ids(client: TestClient, suffix: str) -> None:
    body = {"kb_id": "other", "source_id": "source_1"}
    if suffix == "imports":
        body["expected_preview_hash"] = "sha256:preview"
    response = client.post(f"/v1/kbs/kb1/{suffix}", json=body)
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_every_route_in_openapi_is_registered(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    declared = {(method.upper(), path) for path, ops in paths.items() for method in ops}
    for method, path in declared:
        concrete = path.replace("{kb_id}", "kb").replace("{document_id}", "doc")
        for token in ("{qa_id}", "{version_id}", "{source_id}", "{root_id}", "{batch_id}"):
            concrete = concrete.replace(token, "x")
        for token in ("{session_id}", "{answer_id}", "{citation_id}", "{issue_id}"):
            concrete = concrete.replace(token, "x")
        for token in ("{model_id}", "{profile_id}", "{job_id}"):
            concrete = concrete.replace(token, "x")
        if method == "GET" and path in {"/openapi.json", "/docs", "/redoc"}:
            continue
        response = client.request(method, concrete)
        assert response.status_code != 404, f"{method} {path} is declared but missing"
