
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
    """
    Convert values that are not JSON serializable into safe
    JSON-compatible representations.

    This is especially important for Pydantic validation errors,
    where the `ctx` field may contain a ValueError instance.
    """

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

    # Exceptions such as ValueError are converted to strings.
    if isinstance(value, BaseException):
        return str(value)

    # Final fallback for any unexpected object.
    return str(value)


def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """
    Handle FastAPI HTTPException instances.

    Structured dictionaries supplied by API routes are preserved so
    domain-specific fields such as exception_id and run_id are not lost.
    """

    request_id = _get_request_id(request)

    # --------------------------------------------------------------
    # Preserve structured application errors
    # --------------------------------------------------------------

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

    # --------------------------------------------------------------
    # Handle simple string HTTPException details
    # --------------------------------------------------------------

    logger.warning(
        "http_exception request_id=%s method=%s path=%s "
        "status_code=%s",
        request_id,
        request.method,
        request.url.path,
        exc.status_code,
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
    """
    Handle request validation errors consistently.

    Validation errors are converted into JSON-safe structures because
    Pydantic may include exception objects such as ValueError inside
    the validation context.
    """

    request_id = _get_request_id(request)

    raw_errors = exc.errors()
    safe_errors = _make_json_safe(raw_errors)

    logger.warning(
        "validation_error request_id=%s path=%s errors=%s",
        request_id,
        request.url.path,
        safe_errors,
    )

    payload = {
        "error": "VALIDATION_ERROR",
        "message": "Request validation failed.",
        "details": safe_errors,
    }

    if request_id is not None:
        payload["request_id"] = request_id

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=payload,
    )


def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unexpected application failures.

    Internal exception details are logged server-side but are never
    exposed to API clients.
    """

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

