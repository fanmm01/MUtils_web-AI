"""HTTP error handling: one stable envelope for every failure."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from qa_contracts.errors import APIError, ErrorCode, ErrorDetail, ValidationFailed

REQUEST_ID_HEADER = "X-Request-ID"


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "") or request.headers.get(REQUEST_ID_HEADER, "")


def exception_response(error: APIError, request_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content=error.body(request_id),
        headers={REQUEST_ID_HEADER: request_id},
    )


def install_handlers(app: FastAPI) -> None:
    """Register the API error envelope and validation translation."""

    @app.exception_handler(APIError)
    async def _api_error(request: Request, exc: APIError) -> JSONResponse:
        return exception_response(exc, _request_id(request))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            ErrorDetail(field=".".join(str(part) for part in item["loc"][1:]) or None,
                        reason=item["msg"])
            for item in exc.errors()
        ]
        return exception_response(ValidationFailed(details), _request_id(request))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Never leak a path, credential or stack trace to a web client.
        safe = APIError("internal error")
        safe.code = ErrorCode.INTERNAL_ERROR
        return exception_response(safe, _request_id(request))
