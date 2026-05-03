from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from backend directory when present (local developer workflows).
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


def _read_secret_key() -> str:
    return (os.getenv("SECRET_KEY") or "").strip()


def _read_jwt_secret_key() -> str:
    """Flask-JWT-Extended reads JWT_SECRET_KEY; JWT_SECRET is accepted as an alias."""
    for key in ("JWT_SECRET_KEY", "JWT_SECRET"):
        v = (os.getenv(key) or "").strip()
        if v:
            return v
    return ""


def _read_database_url() -> str:
    return (os.getenv("DATABASE_URL") or "").strip()


def _read_env_name() -> str:
    return os.getenv("FLASK_ENV", "development")


def _read_debug() -> bool:
    return os.getenv("FLASK_DEBUG", "1") == "1"


def _read_jwt_access_expires() -> int:
    return int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "900"))


def _read_jwt_refresh_expires() -> int:
    return int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "604800"))


def _read_bcrypt_rounds() -> int:
    return int(os.getenv("BCRYPT_LOG_ROUNDS", "12"))


def _read_max_content_length() -> int:
    return int(os.getenv("MAX_CONTENT_LENGTH", str(25 * 1024 * 1024)))


@dataclass
class Settings:
    """Flask configuration from the environment (no insecure defaults for secrets)."""

    SECRET_KEY: str = field(default_factory=_read_secret_key)
    ENV: str = field(default_factory=_read_env_name)
    DEBUG: bool = field(default_factory=_read_debug)

    SQLALCHEMY_DATABASE_URI: str = field(default_factory=_read_database_url)
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    JWT_SECRET_KEY: str = field(default_factory=_read_jwt_secret_key)
    JWT_ACCESS_TOKEN_EXPIRES: int = field(default_factory=_read_jwt_access_expires)
    JWT_REFRESH_TOKEN_EXPIRES: int = field(default_factory=_read_jwt_refresh_expires)

    BCRYPT_LOG_ROUNDS: int = field(default_factory=_read_bcrypt_rounds)

    UPLOAD_ROOT: Path = field(
        default_factory=lambda: Path(os.getenv("UPLOAD_ROOT", "uploads"))
    )
    MAX_CONTENT_LENGTH: int = field(default_factory=_read_max_content_length)
