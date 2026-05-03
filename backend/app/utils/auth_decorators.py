"""JWT route decorators that set ``g.current_user`` after authorization checks."""

from __future__ import annotations

from functools import wraps

from flask import g
from flask_jwt_extended import jwt_required

from .auth_utils import load_authenticated_user, require_staff_user


def require_jwt_user(fn):
    """Require a valid JWT whose subject maps to an existing User; sets ``g.current_user``."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user, err = load_authenticated_user()
        if err is not None:
            return err
        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper


def require_staff(fn):
    """Like :func:`require_jwt_user` but require staff or admin role."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user, err = require_staff_user()
        if err is not None:
            return err
        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper
