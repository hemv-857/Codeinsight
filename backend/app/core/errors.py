"""Centralized API error handling."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from http import HTTPStatus
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

REQUEST_ID_HEADER = "X-Request-ID"
MAX_REQUEST_ID_LENGTH = 128
MAX_VALIDATION_MESSAGES = 3

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register API-wide exception handlers."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return expected HTTP errors using the public error envelope."""
    if not isinstance(exc, StarletteHTTPException):
        raise exc

    status_code = int(exc.status_code)
    detail = _string_detail(exc.detail) or _status_phrase(status_code)
    return _error_response(
        request=request,
        status_code=status_code,
        error=_error_code(status_code),
        detail=detail,
        headers=exc.headers,
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return validation failures without leaking request internals."""
    if not isinstance(exc, RequestValidationError):
        raise exc

    detail = _validation_detail(exc.errors())
    return _error_response(
        request=request,
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        error="validation_error",
        detail=detail,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unexpected failures and return a sanitized response."""
    request_id = _request_id(request)
    logger.exception(
        "Unhandled API error",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        },
        exc_info=exc,
    )
    return _error_response(
        request=request,
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        error="internal_server_error",
        detail="Internal server error.",
        request_id=request_id,
    )


def _error_response(
    *,
    request: Request,
    status_code: int | HTTPStatus,
    error: str,
    detail: str,
    headers: Mapping[str, str] | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    resolved_status = int(status_code)
    resolved_request_id = request_id or _request_id(request)
    response_headers = dict(headers or {})
    response_headers[REQUEST_ID_HEADER] = resolved_request_id
    return JSONResponse(
        status_code=resolved_status,
        content={
            "error": error,
            "detail": detail,
            "status_code": resolved_status,
            "request_id": resolved_request_id,
        },
        headers=response_headers,
    )


def _request_id(request: Request) -> str:
    raw_request_id = request.headers.get(REQUEST_ID_HEADER)
    if raw_request_id is None:
        return uuid4().hex

    request_id = raw_request_id.strip()
    if not request_id or len(request_id) > MAX_REQUEST_ID_LENGTH:
        return uuid4().hex
    return request_id


def _string_detail(detail: Any) -> str | None:
    if isinstance(detail, str):
        return detail
    if detail is None:
        return None
    return str(detail)


def _validation_detail(errors: Sequence[dict[str, Any]]) -> str:
    messages: list[str] = []
    for error in errors[:MAX_VALIDATION_MESSAGES]:
        location = _validation_location(error.get("loc"))
        message = str(error.get("msg") or "Invalid value")
        messages.append(f"{location}: {message}" if location else message)
    return "; ".join(messages) if messages else "Request validation failed."


def _validation_location(location: Any) -> str:
    if not isinstance(location, Sequence) or isinstance(location, str):
        return ""
    visible_parts = [str(part) for part in location if part not in {"body", "query", "path"}]
    return ".".join(visible_parts)


def _status_phrase(status_code: int) -> str:
    try:
        return f"{HTTPStatus(status_code).phrase}."
    except ValueError:
        return "Request failed."


def _error_code(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).phrase.lower().replace(" ", "_")
    except ValueError:
        return "http_error"
