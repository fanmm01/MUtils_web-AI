"""FastAPI application factory.

``create_app`` registers routes, middleware and error handlers only. It does not
open a database, start a worker, probe a model runtime or download anything.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from qa_contracts.errors import STATUS_BY_CODE, APIErrorResponse, FeatureNotImplemented

from . import __version__
from .container import build_container, close_container
from .http_errors import REQUEST_ID_HEADER, install_handlers
from .routes import (
    answers,
    content,
    feedback,
    imports,
    knowledge,
    models,
    operations,
    selection,
    sources,
    system,
)
from .settings import Settings, load_settings

ROUTE_MODULES = (
    system,
    knowledge,
    content,
    imports,
    sources,
    answers,
    selection,
    feedback,
    models,
    operations,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or load_settings()
    container = build_container(resolved)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # No discovery, no migrations, no downloads: those are explicit actions.
        yield
        close_container(app.state.container)

    app = FastAPI(
        title="Q&A Assistant API",
        version=__version__,
        description=(
            "P3 contract gate: P2 management routes work in operational mode; "
            "model, answer, conflict resolution and SSE business remain unimplemented."
        ),
        lifespan=lifespan,
    )
    app.state.container = container

    if resolved.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=resolved.allowed_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "Last-Event-ID"],
            expose_headers=[REQUEST_ID_HEADER],
        )

    @app.middleware("http")
    async def _correlate(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

    install_handlers(app)
    for module in ROUTE_MODULES:
        app.include_router(module.router)

    # FastAPI's default 422 shape does not match the installed error handlers.
    # Publish the actual envelope consistently for every declared endpoint.
    error_responses = {
        str(status): {
            "description": "Error response",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/APIErrorResponse"}
                }
            },
        }
        for status in sorted(set(STATUS_BY_CODE.values()) - {200})
    }
    generated_openapi = app.openapi

    def documented_openapi() -> dict[str, object]:
        if app.openapi_schema is not None:
            return app.openapi_schema  # type: ignore[no-any-return]
        schema = generated_openapi()
        components = schema.setdefault("components", {}).setdefault("schemas", {})
        error_schema = APIErrorResponse.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
        components.update(error_schema.pop("$defs", {}))
        components["APIErrorResponse"] = error_schema
        for path, item in schema["paths"].items():
            for operation in item.values():
                if not isinstance(operation, dict) or "responses" not in operation:
                    continue
                responses = operation["responses"]
                for status, response in error_responses.items():
                    if path == "/readyz" and status == "503":
                        continue
                    responses[status] = response
        app.openapi_schema = schema
        return schema

    app.openapi = documented_openapi
    return app


def require_business_capability(feature: str) -> None:
    """Guard used by SSE and other non-JSON entry points before streaming."""
    raise FeatureNotImplemented(feature)
