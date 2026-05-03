"""Consistent JSON error bodies for API responses."""

from __future__ import annotations

from typing import Any

from flask import jsonify

_HTTP_CLIENT_ERRORS: dict[int, str] = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    408: "request_timeout",
    409: "conflict",
    413: "payload_too_large",
    415: "unsupported_media_type",
    422: "unprocessable_entity",
    429: "too_many_requests",
}


def client_error_code(status_code: int) -> str:
    """Stable machine-readable ``error`` field for HTTP client errors (4xx)."""
    return _HTTP_CLIENT_ERRORS.get(status_code, "client_error")


def error_response(
    status_code: int,
    error: str,
    message: str,
    *,
    error_id: str | None = None,
    extra: dict[str, Any] | None = None,
):
    """Return ``(flask.Response, status_code)`` with a standard JSON body."""
    body: dict[str, Any] = {"error": error, "message": message}
    if error_id:
        body["error_id"] = error_id
    if extra:
        body.update(extra)
    resp = jsonify(body)
    resp.status_code = status_code
    return resp, status_code
