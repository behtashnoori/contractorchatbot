"""
Pytest configuration for API security tests.

Integration tests in test_auth_security.py need PostgreSQL (same schema as production):

  set TEST_DATABASE_URL=postgresql+psycopg://user:pass@host:port/dbname_test
  cd backend && flask db upgrade
  pytest tests/

JWT-only tests use a placeholder DATABASE_URL and do not connect to the database.
"""

from __future__ import annotations

import os

import pytest

# Apply before importing the application package so JWT/CORS-related env is stable.
os.environ.setdefault("FLASK_ENV", "development")
os.environ.setdefault("FLASK_DEBUG", "0")
os.environ.setdefault(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)


# Invalid/unreachable host:port — SQLAlchemy only connects on first query (JWT errors do not query).
_PLACEHOLDER_DATABASE_URL = "postgresql+psycopg://127.0.0.1:9/__pytest_jwt_only__"


@pytest.fixture
def app_jwt_only(monkeypatch):
    """Minimal app for routes that fail JWT validation before touching the database."""
    monkeypatch.setenv("DATABASE_URL", _PLACEHOLDER_DATABASE_URL)
    monkeypatch.setenv(
        "SECRET_KEY",
        "pytest-secret-key-at-least-32-characters-long",
    )
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "pytest-jwt-secret-key-at-least-32-chars-long",
    )
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRES", "3600")
    monkeypatch.setenv("JWT_REFRESH_TOKEN_EXPIRES", "86400")

    from app import create_app

    return create_app()


@pytest.fixture
def client_jwt_only(app_jwt_only):
    return app_jwt_only.test_client()


@pytest.fixture
def app(monkeypatch):

    """Flask app wired to TEST_DATABASE_URL with fixed secrets for JWT signing."""
    db_url = (os.environ.get("TEST_DATABASE_URL") or "").strip()
    if not db_url:
        pytest.skip("TEST_DATABASE_URL is not set")

    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv(
        "SECRET_KEY",
        "pytest-secret-key-at-least-32-characters-long",
    )
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "pytest-jwt-secret-key-at-least-32-chars-long",
    )
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRES", "3600")
    monkeypatch.setenv("JWT_REFRESH_TOKEN_EXPIRES", "86400")

    from app import create_app

    application = create_app()
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def app_ctx(app):
    with app.app_context():
        yield app
