import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from .config import Settings
from .extensions import db, migrate, jwt, bcrypt, cors
from .routes.auth import auth_bp
from .routes.invoices import invoices_bp
from .routes.admin import admin_bp

# Load .env file from backend directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
    if not raw:
        if os.getenv("FLASK_ENV", "development") == "production":
            return []
        # Minimal local defaults when unset (development only)
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


ALLOWED_ORIGINS = _parse_cors_origins()


def is_allowed_origin(origin):
    """Allow only origins explicitly listed via CORS_ALLOWED_ORIGINS (or dev fallback)."""
    if not origin:
        return False
    return origin in ALLOWED_ORIGINS


def _configure_logging(app: Flask) -> None:
    level_name = os.getenv("LOG_LEVEL", "DEBUG" if app.debug else "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=level)
    root.setLevel(level)
    app.logger.setLevel(level)


def create_app(settings_override: dict | None = None) -> Flask:
    app = Flask(__name__)

    app.config.from_object(Settings())
    if settings_override:
        app.config.update(settings_override)

    db_uri = (app.config.get("SQLALCHEMY_DATABASE_URI") or "").strip()
    if not db_uri:
        raise RuntimeError("DATABASE_URL must be set in the environment.")

    if os.getenv("FLASK_ENV", "development") == "production":
        if not ALLOWED_ORIGINS:
            raise RuntimeError(
                "CORS_ALLOWED_ORIGINS must be set to a comma-separated list in production."
            )

    _configure_logging(app)

    _init_extensions(app)
    _register_blueprints(app)

    # Error handler for 403 Forbidden to ensure CORS headers
    @app.errorhandler(403)
    def handle_forbidden(e):
        from flask import request, jsonify

        response = jsonify({"error": "forbidden", "message": "Access forbidden"})
        response.status_code = 403
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
        from flask import jsonify, request
        from werkzeug.exceptions import HTTPException

        origin = request.headers.get("Origin")

        if isinstance(e, HTTPException):
            response = jsonify(
                {"error": "http_error", "message": e.description}
            )
            response.status_code = e.code
        else:
            app.logger.exception("Unhandled exception")
            response = jsonify(
                {
                    "error": "internal_server_error",
                    "message": "An unexpected error occurred",
                }
            )
            response.status_code = 500

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
        return response

    return app


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(
        app,
        resources={
            r"/*": {
                "origins": is_allowed_origin,
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
        from flask import request, jsonify

        response = jsonify({"error": "token_expired", "message": "Token has expired"})
        response.status_code = 401
        origin = request.headers.get("Origin")
        if is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
        return response

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        from flask import request, jsonify

        response = jsonify({"error": "invalid_token", "message": "Invalid token"})
        response.status_code = 401
        origin = request.headers.get("Origin")
        if is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
        return response

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        from flask import request, jsonify

        response = jsonify({"error": "unauthorized", "message": "Authorization required"})
        response.status_code = 401
        origin = request.headers.get("Origin")
        if is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
        return response


def _register_blueprints(app: Flask) -> None:
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(invoices_bp, url_prefix="/invoices")
    app.register_blueprint(admin_bp, url_prefix="/admin")
