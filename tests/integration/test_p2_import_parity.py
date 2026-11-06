"""Real API parity for re-imports whose bytes return to an earlier value."""

from __future__ import annotations

import asyncio
import hashlib

from fastapi.testclient import TestClient

from qa_service.worker import run_once


def test_a_b_a_imports_use_new_jobs_but_replay_one_confirmation(api: TestClient) -> None:
    kb_response = api.post("/v1/kbs", json={"name": "baseline parity"})
    assert kb_response.status_code == 201, kb_response.text
    kb_id = kb_response.json()["kb_id"]
    source_id = "src_cycle"
    source = api.post(
        f"/v1/kbs/{kb_id}/sources",
        json={
            "source_id": source_id,
            "kb_id": kb_id,
            "kind": "upload",
            "display_name": "source",
            "revision": "r1",
        },
    )
    assert source.status_code == 201, source.text

    def upload(text: str) -> None:
        payload = text.encode("utf-8")
        batch_response = api.post(
            "/v1/uploads",
            json={
                "source_id": source_id,
                "files": [{
                    "relative_path": "a.md",
                    "digest": hashlib.sha256(payload).hexdigest(),
                    "size": len(payload),
                }],
            },
        )
        assert batch_response.status_code == 202, batch_response.text
        batch_id = batch_response.json()["batch_id"]
        part = api.put(
            f"/v1/uploads/{batch_id}/files",
            params={"relative_path": "a.md"},
            content=payload,
        )
        assert part.status_code == 202, part.text
        completed = api.post(f"/v1/uploads/{batch_id}/complete")
        assert completed.status_code == 202, completed.text
        assert completed.json()["scan_status"] == "succeeded"

    def submit(expected_change: str) -> str:
        body = {"kb_id": kb_id, "source_id": source_id, "mode": "merge", "selection": {}}
        preview = api.post(f"/v1/kbs/{kb_id}/imports/preview", json=body)
        assert preview.status_code == 202, preview.text
        assert preview.json()[expected_change] == ["a.md"]
        confirmed = {**body, "expected_preview_hash": preview.json()["preview_hash"]}
        first = api.post(f"/v1/kbs/{kb_id}/imports", json=confirmed)
        assert first.status_code == 202, first.text
        replay = api.post(f"/v1/kbs/{kb_id}/imports", json=confirmed)
        assert replay.status_code == 202, replay.text
        job_id = first.json()["job_id"]
        assert replay.json()["job_id"] == job_id
        return job_id

    def publish(job_id: str, expected: str | None) -> str:
        assert asyncio.run(run_once(api.app.state.container)) == job_id
        job_response = api.get(f"/v1/jobs/{job_id}")
        assert job_response.status_code == 200, job_response.text
        job = job_response.json()
        assert job["state"] == "succeeded", job
        version_id = job["result_version_id"]
        published = api.post(
            f"/v1/versions/{version_id}/publish",
            json={"expected_active_version_id": expected},
        )
        assert published.status_code == 200, published.text
        return version_id

    upload("# A\n\nfirst\n")
    first_job = submit("added")
    first_version = publish(first_job, None)

    upload("# B\n\nsecond\n")
    second_job = submit("modified")
    assert second_job != first_job
    second_version = publish(second_job, first_version)

    upload("# A\n\nfirst\n")
    third_job = submit("modified")
    assert third_job not in {first_job, second_job}
    third_version = publish(third_job, second_version)
    assert third_version not in {first_version, second_version}
    assert api.get(f"/v1/kbs/{kb_id}").json()["active_version_id"] == third_version
