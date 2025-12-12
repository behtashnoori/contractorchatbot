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


def create_app(settings_override: dict | None = None) -> Flask:
    app = Flask(__name__)

    # load base settings, then override with caller-provided values
    app.config.from_object(Settings())
    if settings_override:
        app.config.update(settings_override)

    _init_extensions(app)
    _register_blueprints(app)

    # Error handler for 403 Forbidden to ensure CORS headers
    @app.errorhandler(403)
    def handle_forbidden(e):
        from flask import request, jsonify
        response = jsonify({"error": "forbidden", "message": "Access forbidden"})
        response.status_code = 403
        origin = request.headers.get('Origin')
        allowed_origins = [
            "http://localhost:8308",
            "http://localhost:3000",
            "http://127.0.0.1:8308",
            "http://127.0.0.1:3000",
        ]
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Access-Control-Request-Method, Access-Control-Request-Headers'
            response.headers['Access-Control-Expose-Headers'] = 'Content-Type, Authorization'
        return response
    
    # Error handler to ensure CORS headers on error responses
    @app.errorhandler(Exception)
    def handle_exception(e):
        from flask import jsonify, request
        # #region agent log
        import json
        import time
        import traceback
        origin = request.headers.get('Origin', 'no-origin') if hasattr(request, 'headers') else 'no-origin'
        error_trace = traceback.format_exc()
        with open('d:\\1-webapp\\19-contractorchatbot\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"id":"log_exception_handler","timestamp":int(time.time()*1000),"location":"__init__.py:handle_exception","message":"Exception caught in error handler","data":{"error":str(e),"origin":origin,"traceback":error_trace},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + '\n')
        # #endregion
        
        # Create error response
        response = jsonify({"error": "internal_server_error", "message": str(e)})
        response.status_code = 500
        
        # Add CORS headers to error response
        allowed_origins = [
            "http://localhost:8308",
            "http://localhost:3000",
            "http://127.0.0.1:8308",
            "http://127.0.0.1:3000",
        ]
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Access-Control-Request-Method, Access-Control-Request-Headers'
            response.headers['Access-Control-Expose-Headers'] = 'Content-Type, Authorization'
        
        return response

    # Add after_request handler to ensure CORS headers on all responses
    # Flask-CORS should handle this automatically, but this ensures consistency
    @app.after_request
    def after_request(response):
        # #region agent log
        import json
        import time
        origin = __import__('flask').request.headers.get('Origin', 'no-origin')
        cors_headers_before = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
        # #endregion
        
        # Manual CORS header injection as fallback
        allowed_origins = [
            "http://localhost:8308",
            "http://localhost:3000",
            "http://127.0.0.1:8308",
            "http://127.0.0.1:3000",
        ]
        
        # Check if origin is allowed (handle None/empty cases)
        origin_to_use = origin if origin and origin != 'no-origin' else None
        if origin_to_use and origin_to_use in allowed_origins:
            # Add CORS headers if not already present
            if 'Access-Control-Allow-Origin' not in response.headers:
                response.headers['Access-Control-Allow-Origin'] = origin_to_use
            if 'Access-Control-Allow-Methods' not in response.headers:
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD'
            if 'Access-Control-Allow-Headers' not in response.headers:
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Access-Control-Request-Method, Access-Control-Request-Headers'
            if 'Access-Control-Expose-Headers' not in response.headers:
                response.headers['Access-Control-Expose-Headers'] = 'Content-Type, Authorization'
        elif origin_to_use:
            # Log if origin is not in allowed list (for debugging)
            # #region agent log
            with open('d:\\1-webapp\\19-contractorchatbot\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"id":"log_origin_not_allowed","timestamp":int(time.time()*1000),"location":"__init__.py:after_request","message":"Origin not in allowed list","data":{"origin":origin_to_use,"allowed_origins":allowed_origins},"sessionId":"debug-session","runId":"run1","hypothesisId":"D"}) + '\n')
            # #endregion
        
        # #region agent log
        cors_headers_after = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
        with open('d:\\1-webapp\\19-contractorchatbot\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"id":"log_after_request","timestamp":int(time.time()*1000),"location":"__init__.py:after_request","message":"After request handler","data":{"origin":origin,"status_code":response.status_code,"cors_headers_before":dict(cors_headers_before),"cors_headers_after":dict(cors_headers_after),"path":__import__('flask').request.path,"method":__import__('flask').request.method},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
        # #endregion
        return response

    return app


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    # CORS configuration - explicit origins for development
    # Using specific origins instead of "*" to avoid conflicts with supports_credentials
    # #region agent log
    import json
    with open('d:\\1-webapp\\19-contractorchatbot\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
        f.write(json.dumps({"id":"log_init_cors","timestamp":int(__import__('time').time()*1000),"location":"__init__.py:_init_extensions","message":"Initializing CORS","data":{"origins":["http://localhost:8308","http://localhost:3000","http://127.0.0.1:8308","http://127.0.0.1:3000"]},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
    # #endregion
    cors.init_app(
        app,
        resources={
            r"/*": {
                "origins": [
                    "http://localhost:8308",
                    "http://localhost:3000",
                    "http://127.0.0.1:8308",
                    "http://127.0.0.1:3000",
                ],
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
    
    # JWT error handlers to ensure CORS headers on auth errors
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        from flask import request, jsonify
        response = jsonify({"error": "token_expired", "message": "Token has expired"})
        response.status_code = 401
        origin = request.headers.get('Origin')
        if origin in ["http://localhost:8308", "http://localhost:3000", "http://127.0.0.1:8308", "http://127.0.0.1:3000"]:
            response.headers['Access-Control-Allow-Origin'] = origin
        return response
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        from flask import request, jsonify
        response = jsonify({"error": "invalid_token", "message": "Invalid token"})
        response.status_code = 401
        origin = request.headers.get('Origin')
        if origin in ["http://localhost:8308", "http://localhost:3000", "http://127.0.0.1:8308", "http://127.0.0.1:3000"]:
            response.headers['Access-Control-Allow-Origin'] = origin
        return response
    
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        from flask import request, jsonify
        response = jsonify({"error": "unauthorized", "message": "Authorization required"})
        response.status_code = 401
        origin = request.headers.get('Origin')
        if origin in ["http://localhost:8308", "http://localhost:3000", "http://127.0.0.1:8308", "http://127.0.0.1:3000"]:
            response.headers['Access-Control-Allow-Origin'] = origin
        return response
    # #region agent log
    with open('d:\\1-webapp\\19-contractorchatbot\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
        f.write(json.dumps({"id":"log_cors_initialized","timestamp":int(__import__('time').time()*1000),"location":"__init__.py:_init_extensions","message":"CORS initialized","data":{},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
    # #endregion


def _register_blueprints(app: Flask) -> None:
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(invoices_bp, url_prefix="/invoices")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    
    # #region agent log
    @app.before_request
    def before_request():
        try:
            import json
            import time
            origin = __import__('flask').request.headers.get('Origin', 'no-origin')
            method = __import__('flask').request.method
            path = __import__('flask').request.path
            log_data = {"id":"log_before_request","timestamp":int(time.time()*1000),"location":"__init__.py:before_request","message":"Before request","data":{"origin":origin,"method":method,"path":path},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}
            with open('d:\\1-webapp\\19-contractorchatbot\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data) + '\n')
        except Exception as e:
            # Fallback: try to log the error
            try:
                import time
                with open('d:\\1-webapp\\19-contractorchatbot\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"id":"log_before_request_error","timestamp":int(time.time()*1000),"location":"__init__.py:before_request","message":"Logging error","data":{"error":str(e)},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + '\n')
            except:
                pass
    # #endregion
    
    # Explicit OPTIONS handler for CORS preflight (Flask-CORS should handle this, but ensure it works)
    @app.before_request
    def handle_options():
        if __import__('flask').request.method == 'OPTIONS':
            # #region agent log
            import json
            import time
            origin = __import__('flask').request.headers.get('Origin', 'no-origin')
            with open('d:\\1-webapp\\19-contractorchatbot\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"id":"log_options_request","timestamp":int(time.time()*1000),"location":"__init__.py:handle_options","message":"OPTIONS preflight request","data":{"origin":origin,"path":__import__('flask').request.path},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + '\n')
            # #endregion
            # Flask-CORS will handle the response, but we log it

