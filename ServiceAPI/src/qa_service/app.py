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

from qa_contracts.errors import FeatureNotImplemented

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
        description="Scaffold build: business endpoints return 501 until later phases.",
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
    return app


def require_business_capability(feature: str) -> None:
    """Guard used by SSE and other non-JSON entry points before streaming."""
    raise FeatureNotImplemented(feature)
