"""Thin HTTP client for the Q&A assistant API.

The client only transports requests and decodes responses. It never re-implements
retrieval, selection, versioning or import rules, and it cannot bypass install
confirmation.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

import httpx

from qa_contracts.errors import APIErrorResponse, ErrorCode, ErrorDetail

from .sse import SSEEvent, decode_sse


class QAError(Exception):
    """Transport-independent error carrying the stable API error fields."""

    def __init__(
        self,
        code: str,
        message: str,
        status: int = 0,
        details: list[ErrorDetail] | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or []
        self.request_id = request_id

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"

    @classmethod
    def from_response(cls, status: int, payload: Any, request_id: str | None) -> QAError:
        try:
            parsed = APIErrorResponse.model_validate(payload)
        except Exception:
            return cls(
                ErrorCode.INTERNAL_ERROR.value,
                "the server returned an unrecognized error payload",
                status=status,
                request_id=request_id,
            )
        return cls(
            parsed.error.code.value,
            parsed.error.message,
            status=status,
            details=parsed.error.details,
            request_id=parsed.request_id or request_id,
        )


class Client:
    """Synchronous client. ``base_url`` must point at a trusted server."""

    def __init__(
        self,
        base_url: str,
        credential: str | None = None,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        headers = {"Accept": "application/json"}
        if credential:
            headers["Authorization"] = f"Bearer {credential}"
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"), headers=headers, timeout=timeout, transport=transport
        )

    # -- plumbing ---------------------------------------------------------
    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        response = self._http.request(method, path, json=json, params=params, headers=headers)
        request_id = response.headers.get("X-Request-ID")
        if response.status_code >= 400:
            raise QAError.from_response(response.status_code, _json_or_none(response), request_id)
        return _json_or_none(response)

    def _get(self, path: str, **kwargs: Any) -> Any:
        return self._request("GET", path, **kwargs)

    def _post(self, path: str, **kwargs: Any) -> Any:
        return self._request("POST", path, **kwargs)

    # -- system -----------------------------------------------------------
    def health(self) -> dict[str, Any]:
        return self._get("/healthz")

    def readiness(self) -> dict[str, Any]:
        return self._get("/readyz")

    def capabilities(self) -> dict[str, Any]:
        return self._get("/v1/capabilities")

    # -- knowledge base ---------------------------------------------------
    def create_kb(self, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._post("/v1/kbs", json=body)

    def list_kbs(self, limit: int = 50, cursor: str | None = None) -> dict[str, Any]:
        return self._get("/v1/kbs", params={"limit": limit, "cursor": cursor})

    def get_kb(self, kb_id: str) -> dict[str, Any]:
        return self._get(f"/v1/kbs/{kb_id}")

    def update_kb(self, kb_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/v1/kbs/{kb_id}", json=body)

    def delete_kb(self, kb_id: str, expected_etag: str | None = None) -> None:
        self._request("DELETE", f"/v1/kbs/{kb_id}", params={"expected_etag": expected_etag})

    # -- content ----------------------------------------------------------
    def create_document(self, kb_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._post(f"/v1/kbs/{kb_id}/documents", json=body)

    def list_documents(
        self, kb_id: str, limit: int = 50, cursor: str | None = None
    ) -> dict[str, Any]:
        return self._get(
            f"/v1/kbs/{kb_id}/documents", params={"limit": limit, "cursor": cursor}
        )

    def get_document(self, document_id: str, revision_id: str | None = None) -> dict[str, Any]:
        return self._get(
            f"/v1/documents/{document_id}", params={"revision_id": revision_id}
        )

    def update_document(self, document_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/v1/documents/{document_id}", json=body)

    def delete_document(self, document_id: str, expected_revision_id: str | None = None) -> Any:
        return self._request(
            "DELETE",
            f"/v1/documents/{document_id}",
            params={"expected_revision_id": expected_revision_id},
        )

    def create_qa(self, kb_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._post(f"/v1/kbs/{kb_id}/qa-pairs", json=body)

    def list_qa(self, kb_id: str, limit: int = 50, cursor: str | None = None) -> dict[str, Any]:
        return self._get(f"/v1/kbs/{kb_id}/qa-pairs", params={"limit": limit, "cursor": cursor})

    # -- imports and versions --------------------------------------------
    def preview_import(self, kb_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._post(f"/v1/kbs/{kb_id}/imports/preview", json=body)

    def import_documents(self, kb_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._post(f"/v1/kbs/{kb_id}/imports", json=body)

    def sync_source(self, source_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._post(f"/v1/sources/{source_id}/sync", json=body)

    def list_versions(self, kb_id: str) -> list[dict[str, Any]]:
        return self._get(f"/v1/kbs/{kb_id}/versions")

    def publish_version(self, version_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._post(f"/v1/versions/{version_id}/publish", json=body)

    def rollback(self, kb_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._post(f"/v1/kbs/{kb_id}/rollback", json=body)

    # -- search / ask -----------------------------------------------------
    def search(
        self, question: str, selection: Mapping[str, Any] | None = None,
        inference: Mapping[str, Any] | None = None, top_k: int = 10,
    ) -> dict[str, Any]:
        return self._post(
            "/v1/search",
            json={
                "question": question,
                "selection": selection,
                "inference": inference,
                "top_k": top_k,
            },
        )

    def ask(
        self,
        question: str,
        selection: Mapping[str, Any] | None = None,
        inference: Mapping[str, Any] | None = None,
        session_id: str | None = None,
        idempotency_key: str | None = None,
        wait_seconds: float = 30.0,
    ) -> dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self._post(
            "/v1/ask",
            json={
                "question": question,
                "selection": selection,
                "inference": inference,
                "session_id": session_id,
                "wait_seconds": wait_seconds,
            },
            headers=headers,
        )

    def create_session(
        self,
        selection: Mapping[str, Any] | None = None,
        inference: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._post(
            "/v1/sessions", json={"selection": selection, "inference": inference}
        )

    def submit_answer(
        self,
        session_id: str,
        question: str,
        selection: Mapping[str, Any] | None = None,
        inference: Mapping[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self._post(
            f"/v1/sessions/{session_id}/answers",
            json={"question": question, "selection": selection, "inference": inference},
            headers=headers,
        )

    def get_answer(self, answer_id: str) -> dict[str, Any]:
        return self._get(f"/v1/answers/{answer_id}")

    def cancel_answer(self, answer_id: str) -> dict[str, Any]:
        return self._post(f"/v1/answers/{answer_id}/cancel")

    def get_citation(self, answer_id: str, citation_id: str) -> dict[str, Any]:
        return self._get(f"/v1/answers/{answer_id}/citations/{citation_id}")

    def get_history(self, session_id: str) -> list[dict[str, Any]]:
        return self._get(f"/v1/sessions/{session_id}/history")

    # -- selection --------------------------------------------------------
    def get_knowledge_catalog(self, limit: int = 50, cursor: str | None = None) -> dict[str, Any]:
        return self._get("/v1/knowledge-catalog", params={"limit": limit, "cursor": cursor})

    def preview_selection(self, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._post("/v1/knowledge-selection/preview", json=body)

    def get_session_selection(self, session_id: str) -> dict[str, Any]:
        return self._get(f"/v1/sessions/{session_id}/selection")

    def set_session_selection(self, session_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/v1/sessions/{session_id}/selection", json=body)

    # -- inference / models ----------------------------------------------
    def get_session_inference(self, session_id: str) -> dict[str, Any]:
        return self._get(f"/v1/sessions/{session_id}/inference")

    def set_session_inference(self, session_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/v1/sessions/{session_id}/inference", json=body)

    def model_capabilities(self) -> dict[str, Any]:
        return self._get("/v1/models/capabilities")

    def discover_runtimes(self, target_ids: list[str]) -> dict[str, Any]:
        return self._post("/v1/models/discovery", json={"target_ids": target_ids})

    def list_runtimes(self) -> list[dict[str, Any]]:
        return self._get("/v1/models/runtimes")

    def list_models(self, **query: Any) -> dict[str, Any]:
        return self._get("/v1/models", params=query)

    def get_model(self, model_id: str) -> dict[str, Any]:
        return self._get(f"/v1/models/{model_id}")

    def list_profiles(self) -> dict[str, Any]:
        return self._get("/v1/inference-profiles")

    def get_profile(self, profile_id: str, revision: str | None = None) -> dict[str, Any]:
        return self._get(f"/v1/inference-profiles/{profile_id}", params={"revision": revision})

    def put_profile(self, body: Mapping[str, Any], profile_id: str | None = None) -> Any:
        if profile_id is None:
            return self._post("/v1/inference-profiles", json=body)
        return self._request("PUT", f"/v1/inference-profiles/{profile_id}", json=body)

    def disable_profile(self, profile_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._post(f"/v1/inference-profiles/{profile_id}/disable", json=body)

    def preview_install(self, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._post("/v1/model-installs/preview", json=body)

    def confirm_install(
        self, body: Mapping[str, Any], idempotency_key: str | None = None
    ) -> dict[str, Any]:
        # Only a preview reference is accepted; there is no bypass method.
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self._post("/v1/model-installs", json=body, headers=headers)

    def verify_model(self, model_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._post(f"/v1/models/{model_id}/verifications", json=body)

    # -- jobs -------------------------------------------------------------
    def get_job(self, job_id: str) -> dict[str, Any]:
        return self._get(f"/v1/jobs/{job_id}")

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        return self._post(f"/v1/jobs/{job_id}/cancel")

    def job_events(self, job_id: str, last_id: int | None = None) -> Iterator[SSEEvent]:
        return self.subscribe_job(job_id, after=last_id)

    def subscribe_answer(self, answer_id: str, after: int | None = None) -> Iterator[SSEEvent]:
        headers = {"Accept": "text/event-stream"}
        if after:
            headers["Last-Event-ID"] = str(after)
        with self._http.stream("GET", f"/v1/answers/{answer_id}/events", headers=headers) as r:
            _raise_for_stream(r)
            yield from decode_sse(r.iter_bytes())

    def subscribe_job(self, job_id: str, after: int | None = None) -> Iterator[SSEEvent]:
        headers = {"Accept": "text/event-stream"}
        if after:
            headers["Last-Event-ID"] = str(after)
        with self._http.stream("GET", f"/v1/jobs/{job_id}/events", headers=headers) as r:
            _raise_for_stream(r)
            yield from decode_sse(r.iter_bytes())

    # -- feedback ---------------------------------------------------------
    def submit_feedback(self, answer_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        return self._post(f"/v1/answers/{answer_id}/feedback", json=body)

    def list_issues(self, **query: Any) -> list[dict[str, Any]]:
        return self._get("/v1/issues", params=query)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def _json_or_none(response: httpx.Response) -> Any:
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        # A proxy or crash page must not surface raw HTML/stack text to callers.
        return None


def _raise_for_stream(response: httpx.Response) -> None:
    if response.status_code >= 400:
        response.read()
        raise QAError.from_response(
            response.status_code, _json_or_none(response), response.headers.get("X-Request-ID")
        )
