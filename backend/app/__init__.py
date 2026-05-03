import logging
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from .config import Settings
from .extensions import db, migrate, jwt, bcrypt, cors
from .utils.api_errors import client_error_code, error_response
from .routes.auth import auth_bp
from .routes.invoices import invoices_bp
from .routes.admin import admin_bp

# Load .env file from backend directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


def _parse_cors_origins_required() -> list[str]:
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
    if not raw:
        raise RuntimeError(
            "CORS_ALLOWED_ORIGINS must be set to a comma-separated list of allowed origins."
        )
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if not origins:
        raise RuntimeError(
            "CORS_ALLOWED_ORIGINS must be set to a comma-separated list of allowed origins."
        )
    return origins


def is_allowed_origin(origin) -> bool:
    """Allow only origins explicitly listed via CORS_ALLOWED_ORIGINS."""
    if not origin:
        return False
    from flask import has_app_context, current_app

    if not has_app_context():
        return False
    allowed = current_app.config.get("CORS_ALLOWED_ORIGINS_LIST") or []
    return origin in allowed


# Reject common unsafe literals (exact match). No default secrets in Settings.
_PLACEHOLDER_SECRET_KEYS = frozenset(
    {"", "change-me", "changeme", "secret", "your-secret-here", "dev"}
)
_PLACEHOLDER_JWT_KEYS = frozenset(
    {"", "change-me-asap", "changeme", "secret", "your-secret-here", "dev"}
)
_MIN_SECRET_LEN = 32


def _validate_environment(app: Flask) -> None:
    """
    Fail fast: require DATABASE_URL, SECRET_KEY, JWT secret, and CORS.
    Rejects empty values, known placeholders, and short secrets in all environments.
    """
    db_uri = (app.config.get("SQLALCHEMY_DATABASE_URI") or "").strip()
    if not db_uri:
        raise RuntimeError("DATABASE_URL must be set to a non-empty value.")

    sk = (app.config.get("SECRET_KEY") or "").strip()
    if not sk:
        raise RuntimeError("SECRET_KEY must be set to a non-empty value.")
    if sk in _PLACEHOLDER_SECRET_KEYS:
        raise RuntimeError("SECRET_KEY must not use a placeholder or trivial value.")
    if len(sk) < _MIN_SECRET_LEN:
        raise RuntimeError(
            f"SECRET_KEY must be at least {_MIN_SECRET_LEN} characters (use a long random value)."
        )

    jwtk = (app.config.get("JWT_SECRET_KEY") or "").strip()
    if not jwtk:
        raise RuntimeError(
            "JWT_SECRET_KEY (or JWT_SECRET) must be set to a non-empty value."
        )
    if jwtk in _PLACEHOLDER_JWT_KEYS:
        raise RuntimeError("JWT signing key must not use a placeholder or trivial value.")
    if len(jwtk) < _MIN_SECRET_LEN:
        raise RuntimeError(
            f"JWT_SECRET_KEY must be at least {_MIN_SECRET_LEN} characters (use a long random value)."
        )

    cors_origins = _parse_cors_origins_required()
    app.config["CORS_ALLOWED_ORIGINS_LIST"] = cors_origins


def _validate_production_security(app: Flask) -> None:
    """Extra rules when FLASK_ENV is production (DEBUG must be off)."""
    if os.getenv("FLASK_ENV", "development") != "production":
        return
    if app.config.get("DEBUG"):
        raise RuntimeError("DEBUG must be disabled in production (set FLASK_DEBUG=0).")


def _validate_runtime_settings(app: Flask) -> None:
    """Validate numeric and size-related config after Settings are loaded."""
    rounds = app.config.get("BCRYPT_LOG_ROUNDS")
    if not isinstance(rounds, int) or rounds < 10 or rounds > 16:
        raise RuntimeError(
            "BCRYPT_LOG_ROUNDS must be an integer from 10 to 16 inclusive."
        )
    access = app.config.get("JWT_ACCESS_TOKEN_EXPIRES")
    refresh = app.config.get("JWT_REFRESH_TOKEN_EXPIRES")
    if not isinstance(access, int) or access <= 0:
        raise RuntimeError("JWT_ACCESS_TOKEN_EXPIRES must be a positive integer (seconds).")
    if not isinstance(refresh, int) or refresh <= 0:
        raise RuntimeError(
            "JWT_REFRESH_TOKEN_EXPIRES must be a positive integer (seconds)."
        )
    mcl = app.config.get("MAX_CONTENT_LENGTH")
    if not isinstance(mcl, int) or mcl <= 0:
        raise RuntimeError("MAX_CONTENT_LENGTH must be a positive integer.")


_DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_DEFAULT_LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"


def _configure_logging(app: Flask) -> None:
    # In production, prefer a reverse proxy or Werkzeug config so access logs
    # do not retain Authorization headers.
    level_name = os.getenv("LOG_LEVEL", "DEBUG" if app.debug else "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    fmt = (os.getenv("LOG_FORMAT") or _DEFAULT_LOG_FORMAT).strip() or _DEFAULT_LOG_FORMAT
    datefmt = (os.getenv("LOG_DATEFMT") or _DEFAULT_LOG_DATEFMT).strip() or _DEFAULT_LOG_DATEFMT
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(formatter)
        root.addHandler(handler)
    else:
        for handler in root.handlers:
            if handler.formatter is None:
                handler.setFormatter(formatter)
    app.logger.setLevel(level)


def create_app(settings_override: dict | None = None) -> Flask:
    app = Flask(__name__)

    app.config.from_object(Settings())
    if settings_override:
        app.config.update(settings_override)

    _validate_environment(app)
    _validate_production_security(app)
    _validate_runtime_settings(app)

    cors_origins = app.config["CORS_ALLOWED_ORIGINS_LIST"]

    _configure_logging(app)

    _init_extensions(app, cors_origins)
    _register_blueprints(app)

    # Error handler for 403 Forbidden to ensure CORS headers
    @app.errorhandler(403)
    def handle_forbidden(e):
        from flask import request

        response, _ = error_response(403, "forbidden", "Access forbidden")
        origin = request.headers.get("Origin")
        if is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Requested-With, Accept, Origin, "
                "Access-Control-Request-Method, Access-Control-Request-Headers"
            )
            response.headers["Access-Control-Expose-Headers"] = (
                "Content-Type, Authorization"
            )
        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        from flask import request
        from jwt.exceptions import PyJWTError
        from werkzeug.exceptions import HTTPException

        if isinstance(e, PyJWTError):
            response, _ = error_response(401, "invalid_token", "Invalid token")
            origin = request.headers.get("Origin")
            if is_allowed_origin(origin):
                response.headers["Access-Control-Allow-Origin"] = origin
            return response

        origin = request.headers.get("Origin")

        if isinstance(e, HTTPException):
            code = e.code or 500
            if code >= 500:
                error_id = str(uuid.uuid4())
                app.logger.exception("HTTP exception [%s]", error_id)
                response, _ = error_response(
                    code,
                    "internal_error",
                    "An unexpected error occurred",
                    error_id=error_id,
                )
            else:
                err_key = client_error_code(code)
                response, _ = error_response(code, err_key, e.description or "")
        else:
            error_id = str(uuid.uuid4())
            app.logger.exception("Unhandled exception [%s]", error_id)
            response, _ = error_response(
                500,
                "internal_error",
                "An unexpected error occurred",
                error_id=error_id,
            )

        if origin and is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Requested-With, Accept, Origin, "
                "Access-Control-Request-Method, Access-Control-Request-Headers"
            )
            response.headers["Access-Control-Expose-Headers"] = (
                "Content-Type, Authorization"
            )
        return response

    @app.after_request
    def after_request(response):
        from flask import request

        origin = request.headers.get("Origin")
        if origin and is_allowed_origin(origin):
            if "Access-Control-Allow-Origin" not in response.headers:
                response.headers["Access-Control-Allow-Origin"] = origin
            if "Access-Control-Allow-Methods" not in response.headers:
                response.headers["Access-Control-Allow-Methods"] = (
                    "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
                )
            if "Access-Control-Allow-Headers" not in response.headers:
                response.headers["Access-Control-Allow-Headers"] = (
                    "Content-Type, Authorization, X-Requested-With, Accept, Origin, "
                    "Access-Control-Request-Method, Access-Control-Request-Headers"
                )
            if "Access-Control-Expose-Headers" not in response.headers:
                response.headers["Access-Control-Expose-Headers"] = (
                    "Content-Type, Authorization"
                )
        # Minimal CSP for JSON API responses (SPA is served separately).
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        )
        return response

    return app


def _init_extensions(app: Flask, cors_origins: list[str]) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(
        app,
        resources={
            r"/*": {
                # Use explicit list (not a callable) so flask-cors error paths do not
                # mis-handle origins when resolving exceptions (see flask-cors 5 / PyJWT).
                "origins": cors_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
                "allow_headers": [
                    "Content-Type",
                    "Authorization",
                    "X-Requested-With",
                    "Accept",
                    "Origin",
                    "Access-Control-Request-Method",
                    "Access-Control-Request-Headers",
                ],
                "expose_headers": ["Content-Type", "Authorization"],
                "supports_credentials": False,
                "max_age": 3600,
            }
        },
    )

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        from flask import request

        response, _ = error_response(401, "token_expired", "Token has expired")
        origin = request.headers.get("Origin")
        if is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
        return response

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        from flask import request

        # Never log ``error`` (may echo token-adjacent material from PyJWT).
        response, _ = error_response(401, "invalid_token", "Invalid token")
        origin = request.headers.get("Origin")
        if is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
        return response

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        from flask import request

        response, _ = error_response(
            401,
            "missing_authorization",
            "Authorization required",
        )
        origin = request.headers.get("Origin")
        if is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
        return response


def _register_blueprints(app: Flask) -> None:
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(invoices_bp, url_prefix="/invoices")
    app.register_blueprint(admin_bp, url_prefix="/admin")
