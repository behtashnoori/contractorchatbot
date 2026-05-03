from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from backend directory when present (local development only).
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


@dataclass
class Settings:
    """Default Flask configuration."""

    # Flask core
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")
    ENV: str = os.getenv("FLASK_ENV", "development")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "1") == "1"

    # SQLAlchemy — DATABASE_URL is required at runtime (validated in create_app)
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", "")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-asap")
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "900"))
    JWT_REFRESH_TOKEN_EXPIRES: int = int(
        os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "604800")
    )

    # Password hashing
    BCRYPT_LOG_ROUNDS: int = int(os.getenv("BCRYPT_LOG_ROUNDS", "12"))

    # Uploads
    UPLOAD_ROOT: Path = Path(os.getenv("UPLOAD_ROOT", "uploads"))
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", str(25 * 1024 * 1024)))
