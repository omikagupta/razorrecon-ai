import logging
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str | None:
    """Return the request ID assigned by request logging middleware."""
    return getattr(request.state, "request_id", None)


def _make_json_safe(value: Any) -> Any:
    """Convert values into JSON-serializable representations."""

    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {
            str(key): _make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            _make_json_safe(item)
            for item in value
        ]

    if isinstance(value, BaseException):
        return str(value)

    return str(value)


def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Handle FastAPI HTTP exceptions consistently."""

    request_id = _get_request_id(request)

    if isinstance(exc.detail, dict):
        payload = _make_json_safe(exc.detail)

        if request_id is not None:
            payload.setdefault("request_id", request_id)

        logger.warning(
            "http_exception request_id=%s method=%s path=%s "
            "status_code=%s error=%s",
            request_id,
            request.method,
            request.url.path,
            exc.status_code,
            payload.get("error", "HTTP_ERROR"),
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=payload,
            headers=getattr(exc, "headers", None),
        )

    payload = {
        "error": "HTTP_ERROR",
        "message": str(exc.detail),
    }

    if request_id is not None:
        payload["request_id"] = request_id

    return JSONResponse(
        status_code=exc.status_code,
        content=payload,
        headers=getattr(exc, "headers", None),
    )


def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle request validation errors consistently."""

    request_id = _get_request_id(request)

    safe_errors = _make_json_safe(exc.errors())

    payload = {
        "error": "VALIDATION_ERROR",
        "message": "Request validation failed.",
        "details": safe_errors,
    }

    if request_id is not None:
        payload["request_id"] = request_id

    logger.warning(
        "validation_error request_id=%s path=%s errors=%s",
        request_id,
        request.url.path,
        safe_errors,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=payload,
    )


def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected application failures safely."""

    request_id = _get_request_id(request)

    logger.exception(
        "unhandled_exception request_id=%s method=%s path=%s",
        request_id,
        request.method,
        request.url.path,
    )

    payload = {
        "error": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected internal error occurred.",
    }

    if request_id is not None:
        payload["request_id"] = request_id

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=payload,
    )