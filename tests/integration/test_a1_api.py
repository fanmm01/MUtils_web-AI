"""A1 HTTP integration: real API over a migrated temporary database.

The ``api`` fixture lives in ``tests/integration/conftest.py``: it migrates the
schema first and starts the app in ``operational`` mode.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient


def _create_kb(client: TestClient, name: str = "产品") -> dict[str, object]:
    response = client.post("/v1/kbs", json={"name": name, "description": "测试库"})
    assert response.status_code == 201, response.text
    return response.json()


def _document(client: TestClient, kb_id: str, title: str, text: str) -> dict[str, object]:
    response = client.post(
        f"/v1/kbs/{kb_id}/documents",
        json={"kb_id": kb_id, "title": title, "text": text},
    )
    assert response.status_code == 202, response.text
    return response.json()


def test_health_and_capabilities_report_operational(api: TestClient) -> None:
    assert api.get("/healthz").json()["mode"] == "operational"
    body = api.get("/v1/capabilities").json()
    assert "knowledge" in body["implemented"]
    assert "models" in body["unimplemented"]
    assert "search" in body["unimplemented"]


def test_kb_crud_and_conflicts(api: TestClient) -> None:
    kb = _create_kb(api)
    assert kb["active_version_id"] is None
    listed = api.get("/v1/kbs").json()
    assert [item["kb_id"] for item in listed["items"]] == [kb["kb_id"]]

    updated = api.patch(
        f"/v1/kbs/{kb['kb_id']}?expected_etag={kb['etag']}",
        json={"name": "产品二部", "domain_tags": ["产品"]},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "产品二部"
    stale = api.patch(
        f"/v1/kbs/{kb['kb_id']}?expected_etag={kb['etag']}", json={"name": "stale"}
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "CONFLICT"

    missing = api.get("/v1/kbs/kb_missing")
    assert missing.status_code == 404
    deleted = api.delete(f"/v1/kbs/{kb['kb_id']}")
    assert deleted.status_code == 202
    assert api.get(f"/v1/kbs/{kb['kb_id']}").status_code == 404


def test_document_and_qa_crud(api: TestClient) -> None:
    kb = _create_kb(api)
    receipt = _document(api, kb["kb_id"], "手册", "第一版正文")
    document_id = receipt["document_id"]
    detail = api.get(f"/v1/documents/{document_id}").json()
    assert detail["revision"]["normalized_text"] == "第一版正文"

    revision_id = detail["document"]["latest_revision_id"]
    updated = api.patch(
        f"/v1/documents/{document_id}",
        json={
            "kb_id": kb["kb_id"], "title": "手册", "text": "第二版正文",
            "expected_revision_id": revision_id,
        },
    )
    assert updated.status_code == 200, updated.text
    assert api.get(f"/v1/documents/{document_id}").json()["revision"]["normalized_text"] == (
        "第二版正文"
    )
    stale = api.patch(
        f"/v1/documents/{document_id}",
        json={
            "kb_id": kb["kb_id"], "title": "手册", "text": "并发修改",
            "expected_revision_id": revision_id,
        },
    )
    assert stale.status_code == 409

    qa = api.post(
        f"/v1/kbs/{kb['kb_id']}/qa-pairs",
        json={"kb_id": kb["kb_id"], "question": "怎么安装？", "answer": "下载安装"},
    )
    assert qa.status_code == 202, qa.text
    pair = api.get(f"/v1/qa-pairs/{qa.json()['document_id']}").json()
    assert pair["question"] == "怎么安装？"
    removed = api.delete(
        f"/v1/qa-pairs/{pair['qa_id']}?expected_revision_id={pair['revision_id']}"
    )
    assert removed.status_code == 200, removed.text
    assert api.get(f"/v1/qa-pairs/{pair['qa_id']}").status_code == 404


def test_upload_import_publish_and_versions(api: TestClient, tmp_path: Path) -> None:
    kb = _create_kb(api)
    source = api.post(
        f"/v1/kbs/{kb['kb_id']}/sources",
        json={
            "source_id": "src_upload", "kb_id": kb["kb_id"], "kind": "upload",
            "display_name": "上传目录", "revision": "r1",
        },
    )
    assert source.status_code == 201, source.text

    payload = "# 安装\n\n先下载安装包。\n".encode()
    manifest = {
        "source_id": "src_upload",
        "files": [{
            "relative_path": "install.md",
            "digest": hashlib.sha256(payload).hexdigest(),
            "size": len(payload),
        }],
    }
    batch = api.post("/v1/uploads", json=manifest)
    assert batch.status_code == 202, batch.text
    batch_id = batch.json()["batch_id"]
    put = api.put(
        f"/v1/uploads/{batch_id}/files",
        params={"relative_path": "install.md"},
        content=payload,
    )
    assert put.status_code == 202, put.text
    completed = api.post(f"/v1/uploads/{batch_id}/complete")
    assert completed.status_code == 202, completed.text
    assert completed.json()["complete"] is True
    assert completed.json()["files"][0]["relative_path"] == "install.md"

    preview = api.post(
        f"/v1/kbs/{kb['kb_id']}/imports/preview",
        json={"kb_id": kb["kb_id"], "source_id": "src_upload"},
    )
    assert preview.status_code == 202, preview.text
    assert preview.json()["added"] == ["install.md"]
    applied = api.post(
        f"/v1/kbs/{kb['kb_id']}/imports",
        json={
            "kb_id": kb["kb_id"], "source_id": "src_upload",
            "expected_preview_hash": preview.json()["preview_hash"],
        },
    )
    assert applied.status_code == 202, applied.text
    job_id = applied.json()["job_id"]

    from qa_service.worker import run_once

    container = api.app.state.container
    import asyncio

    assert asyncio.run(run_once(container)) == job_id
    job = api.get(f"/v1/jobs/{job_id}").json()
    assert job["state"] == "succeeded", job
    version_id = job["result_version_id"]

    versions = api.get(f"/v1/kbs/{kb['kb_id']}/versions").json()
    assert [item["version_id"] for item in versions] == [version_id]
    published = api.post(
        f"/v1/versions/{version_id}/publish", json={"expected_active_version_id": None}
    )
    assert published.status_code == 200, published.text
    assert published.json()["state"] == "published"
    assert api.get(f"/v1/kbs/{kb['kb_id']}").json()["active_version_id"] == version_id

    diff = api.get(
        f"/v1/kbs/{kb['kb_id']}/version-diff",
        params={"left": version_id, "right": version_id},
    )
    assert diff.status_code == 200, diff.text
    assert diff.json()["added"] == []


def test_uploaded_bytes_must_match_the_manifest(api: TestClient) -> None:
    kb = _create_kb(api)
    api.post(
        f"/v1/kbs/{kb['kb_id']}/sources",
        json={
            "source_id": "src_bad", "kb_id": kb["kb_id"], "kind": "upload",
            "display_name": "坏上传", "revision": "r1",
        },
    )
    batch = api.post(
        "/v1/uploads",
        json={
            "source_id": "src_bad",
            "files": [{"relative_path": "x.md", "digest": "0" * 64, "size": 3}],
        },
    ).json()["batch_id"]
    response = api.put(
        f"/v1/uploads/{batch}/files",
        params={"relative_path": "x.md"},
        content=b"abc",
    )
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"
    completed = api.post(f"/v1/uploads/{batch}/complete").json()
    assert completed["complete"] is False or completed["scan_status"] == "failed"


def test_unauthorized_upload_path_is_rejected(api: TestClient) -> None:
    kb = _create_kb(api)
    api.post(
        f"/v1/kbs/{kb['kb_id']}/sources",
        json={
            "source_id": "src_u", "kb_id": kb["kb_id"], "kind": "upload",
            "display_name": "u", "revision": "r1",
        },
    )
    batch = api.post(
        "/v1/uploads",
        json={"source_id": "src_u", "files": []},
    ).json()["batch_id"]
    rejected = api.put(
        f"/v1/uploads/{batch}/files",
        params={"relative_path": "../escape.md"},
        content=b"x",
    )
    assert rejected.status_code == 422


def test_job_events_and_cancel(api: TestClient) -> None:
    kb = _create_kb(api)
    api.post(
        f"/v1/kbs/{kb['kb_id']}/sources",
        json={
            "source_id": "src_j", "kb_id": kb["kb_id"], "kind": "upload",
            "display_name": "j", "revision": "r1",
        },
    )
    batch = api.post("/v1/uploads", json={"source_id": "src_j", "files": []}).json()
    api.post(f"/v1/uploads/{batch['batch_id']}/complete")
    preview = api.post(
        f"/v1/kbs/{kb['kb_id']}/imports/preview",
        json={"kb_id": kb["kb_id"], "source_id": "src_j"},
    ).json()
    applied = api.post(
        f"/v1/kbs/{kb['kb_id']}/imports",
        json={
            "kb_id": kb["kb_id"], "source_id": "src_j",
            "expected_preview_hash": preview["preview_hash"],
        },
    ).json()
    events = api.get(f"/v1/jobs/{applied['job_id']}/events").json()
    assert events == []
    cancelled = api.post(f"/v1/jobs/{applied['job_id']}/cancel")
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["state"] == "cancelled"
    replay = api.get(
        f"/v1/jobs/{applied['job_id']}/events", headers={"Last-Event-ID": "0"}
    ).json()
    assert [event["event"] for event in replay] == ["job.cancelled"]
    assert replay[0]["id"] == 1


def test_business_routes_still_501_for_unimplemented_areas(api: TestClient) -> None:
    for method, path, payload in (
        ("POST", "/v1/search", {"question": "q"}),
        ("GET", "/v1/knowledge-catalog", None),
        ("GET", "/v1/models", None),
    ):
        response = api.request(method, path, json=payload)
        assert response.status_code == 501, (path, response.text)
        assert response.json()["error"]["code"] == "FEATURE_NOT_IMPLEMENTED"


def test_cli_upload_directory_completes_import(api: TestClient, tmp_path: Path) -> None:
    """The CLI uploads a real directory; the server job then builds the version."""
    import asyncio

    from qa_client import Client
    from qa_client.files import upload_directory
    from qa_service.worker import run_once

    kb = _create_kb(api)
    api.post(
        f"/v1/kbs/{kb['kb_id']}/sources",
        json={
            "source_id": "src_cli", "kb_id": kb["kb_id"], "kind": "upload",
            "display_name": "CLI 上传", "revision": "r1",
        },
    )
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "guide.md").write_text("# 指南\n\n先安装再配置。\n", encoding="utf-8")
    with Client("http://testserver", transport=_asgi_transport(api)) as client:
        result = upload_directory(
            client, corpus, source_id="src_cli", kb_id=str(kb["kb_id"])
        )
    assert result["added"] == ["guide.md"]
    assert result["job_id"]

    assert asyncio.run(run_once(api.app.state.container)) == result["job_id"]
    job = api.get(f"/v1/jobs/{result['job_id']}").json()
    assert job["state"] == "succeeded", job


def _asgi_transport(client: TestClient):  # type: ignore[no-untyped-def]
    """Synchronous bridge so the sync SDK exercises the real ASGI app."""
    import asyncio

    import httpx

    inner = httpx.ASGITransport(app=client.app)  # type: ignore[attr-defined]

    class _SyncTransport(httpx.BaseTransport):
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            async def call() -> httpx.Response:
                return await inner.handle_async_request(request)

            response = asyncio.run(call())
            # The sync client requires a sync byte stream: buffer the body.
            asyncio.run(response.aread())
            return httpx.Response(
                response.status_code,
                headers=response.headers,
                content=response.content,
                request=request,
            )

        def close(self) -> None:
            asyncio.run(inner.aclose())

    return _SyncTransport()


def test_documents_and_qa_pairs_enter_a_rebuilt_snapshot(api: TestClient) -> None:
    """Directly entered content must reach a snapshot, not only file imports."""
    kb = _create_kb(api)
    document = _document(api, kb["kb_id"], "手册", "安装前请先备份配置。")
    qa = api.post(
        f"/v1/kbs/{kb['kb_id']}/qa-pairs",
        json={"kb_id": kb["kb_id"], "question": "怎么备份？", "answer": "复制配置文件。"},
    )
    assert qa.status_code == 202, qa.text
    qa_version = qa.json()["version_id"]
    assert qa_version, "content changes must produce a ready snapshot"
    assert qa.json()["job_id"] is None, "the rebuild is synchronous, not a job"

    versions = api.get(f"/v1/kbs/{kb['kb_id']}/versions").json()
    latest = [item for item in versions if item["version_id"] == qa_version][0]
    assert latest["state"] == "ready"
    assert set(latest["document_revisions"]) == {
        document["document_id"],
        qa.json()["document_id"],
    }

    chunks = _snapshot_chunks(api, kb["kb_id"], qa_version)
    texts = [chunk["text"] for chunk in chunks]
    assert any("备份" in text for text in texts)
    assert any(text.startswith("Question: 怎么备份？") for text in texts)

    published = api.post(
        f"/v1/versions/{qa_version}/publish", json={"expected_active_version_id": None}
    )
    assert published.status_code == 200, published.text
    assert api.get(f"/v1/kbs/{kb['kb_id']}").json()["active_version_id"] == qa_version

    # A later edit rebuilds from the whole base and keeps both content kinds.
    edited = api.patch(
        f"/v1/documents/{document['document_id']}",
        json={
            "kb_id": kb["kb_id"], "title": "手册", "text": "安装前请先备份配置与服务清单。",
            "expected_revision_id": api.get(
                f"/v1/documents/{document['document_id']}"
            ).json()["document"]["latest_revision_id"],
        },
    )
    assert edited.status_code == 200, edited.text
    next_version = edited.json()["version_id"]
    assert next_version and next_version != qa_version
    next_texts = [chunk["text"] for chunk in _snapshot_chunks(api, kb["kb_id"], next_version)]
    assert any("服务清单" in text for text in next_texts)
    assert any(text.startswith("Question: 怎么备份？") for text in next_texts)


def test_deleted_qa_pair_leaves_the_next_snapshot(api: TestClient) -> None:
    kb = _create_kb(api)
    _document(api, kb["kb_id"], "保留文档", "这段正文应当留在快照里。")
    qa = api.post(
        f"/v1/kbs/{kb['kb_id']}/qa-pairs",
        json={"kb_id": kb["kb_id"], "question": "旧问题", "answer": "旧答案"},
    ).json()
    pair = api.get(f"/v1/qa-pairs/{qa['document_id']}").json()
    deleted = api.delete(
        f"/v1/qa-pairs/{pair['qa_id']}?expected_revision_id={pair['revision_id']}"
    )
    assert deleted.status_code == 200, deleted.text
    version = deleted.json()["version_id"]
    assert version, "the remaining document must still rebuild a snapshot"
    texts = [chunk["text"] for chunk in _snapshot_chunks(api, kb["kb_id"], version)]
    assert not any("旧问题" in text for text in texts)
    assert any("这段正文" in text for text in texts)


def _snapshot_chunks(api: TestClient, kb_id: str, version_id: str) -> list[dict]:
    import asyncio

    files = api.app.state.container.snapshot_files
    chunks = asyncio.run(files.load_all_chunks(kb_id, version_id))
    return [chunk.model_dump() for chunk in chunks]


def test_kb_delete_is_refused_while_content_exists(api: TestClient) -> None:
    kb = _create_kb(api, name="有内容")
    api.post(
        f"/v1/kbs/{kb['kb_id']}/sources",
        json={
            "source_id": "src_del_api", "kb_id": kb["kb_id"], "kind": "upload",
            "display_name": "d", "revision": "r1",
        },
    )
    refused = api.delete(f"/v1/kbs/{kb['kb_id']}")
    assert refused.status_code == 409, refused.text
    assert refused.json()["error"]["code"] == "CONFLICT"
    assert api.get(f"/v1/kbs/{kb['kb_id']}").status_code == 200

    api.delete("/v1/sources/src_del_api")
    deleted = api.delete(f"/v1/kbs/{kb['kb_id']}")
    assert deleted.status_code == 202, deleted.text
    assert api.get(f"/v1/kbs/{kb['kb_id']}").status_code == 404
