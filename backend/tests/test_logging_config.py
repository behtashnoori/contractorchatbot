from __future__ import annotations

import logging

from app import _DEFAULT_LOG_FORMAT, _build_log_formatter


def test_log_formatter_falls_back_for_json_literal():
    formatter = _build_log_formatter("json", "%Y-%m-%d")
    record = logging.LogRecord(
        name="pytest",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )

    assert formatter._style._fmt == _DEFAULT_LOG_FORMAT
    assert "hello" in formatter.format(record)


def test_log_formatter_accepts_valid_percent_style():
    formatter = _build_log_formatter("%(levelname)s:%(message)s", "%Y-%m-%d")
    record = logging.LogRecord(
        name="pytest",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )

    assert formatter.format(record) == "INFO:hello"


def test_create_app_does_not_crash_with_invalid_log_format(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://127.0.0.1:9/__pytest_logging__")
    monkeypatch.setenv("SECRET_KEY", "pytest-secret-key-at-least-32-characters-long")
    monkeypatch.setenv("JWT_SECRET_KEY", "pytest-jwt-secret-key-at-least-32-chars-long")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRES", "3600")
    monkeypatch.setenv("JWT_REFRESH_TOKEN_EXPIRES", "86400")
    monkeypatch.setenv("LOG_FORMAT", "json")

    from app import create_app

    app = create_app()

    assert app is not None
