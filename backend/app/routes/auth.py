from __future__ import annotations

import uuid

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)

from ..extensions import db
from ..models import Contractor, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username: str | None = payload.get("username")
    password: str | None = payload.get("password")

    if not username or not password:
        return jsonify({"error": "missing_credentials"}), 400

    user: User | None = User.query.filter_by(username=username.lower()).first()
    if user is None:
        return jsonify({
            "error": "not_found",
            "message": "اطلاعات شما در سیستم یافت نشد. لطفاً با کارشناس بازرگانی تماس بگیرید."
        }), 401
    
    if not user.check_password(password):
        return jsonify({
            "error": "invalid_credentials",
            "message": "اطلاعات شما در سیستم یافت نشد. لطفاً با کارشناس بازرگانی تماس بگیرید."
        }), 401

    # For admin/expert users without contractor, allow login
    contractor: Contractor | None = user.contractor
    if contractor and contractor.status != "فعال":
        return jsonify({
            "error": "inactive_contractor",
            "message": "حساب کاربری شما غیرفعال است. لطفاً با کارشناس بازرگانی تماس بگیرید."
        }), 403

    user.last_login_at = db.func.now()
    db.session.commit()

    access_token = create_access_token(identity=user.id.hex)
    refresh_token = create_refresh_token(identity=user.id.hex)

    response_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "must_change_password": user.must_change_password,
    }
    
    # Include contractor info if available
    if contractor:
        response_data["contractor"] = {
            "detail_code": contractor.detail_code,
            "name": contractor.name,
            "status": contractor.status,
        }
    else:
        response_data["contractor"] = None

    return jsonify(response_data), 200


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    identity = get_jwt_identity()
    try:
        user_id = uuid.UUID(identity) if isinstance(identity, str) else identity
    except (ValueError, TypeError):
        return jsonify({"error": "invalid_token"}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "not_found"}), 404

    # Handle users without contractor (admin/expert users)
    if not user.contractor:
        return (
            jsonify(
                {
                    "user": {
                        "username": user.username,
                        "last_login_at": user.last_login_at,
                    },
                    "contractor": None,
                    "totals": {
                        "total_invoices": 0,
                        "pending_amount": 0,
                        "approved_amount": 0,
                    },
                }
            ),
            200,
        )

    contractor = user.contractor
    # Placeholder aggregates until services are implemented
    totals = {
        "total_invoices": contractor.invoice_summaries.count(),
        "pending_amount": 0,
        "approved_amount": 0,
    }

    return (
        jsonify(
            {
                "user": {
                    "username": user.username,
                    "last_login_at": user.last_login_at,
                },
                "contractor": {
                    "detail_code": contractor.detail_code,
                    "name": contractor.name,
                    "status": contractor.status,
                },
                "totals": totals,
            }
        ),
        200,
    )


@auth_bp.post("/change-password")
@jwt_required()
def change_password():
    """
    تغییر رمز عبور - فقط برای admin/expert users.
    Contractor users نمی‌توانند رمز عبور خود را تغییر دهند.
    """
    identity = get_jwt_identity()
    user = User.query.get(identity)
    if not user:
        return jsonify({"error": "not_found"}), 404

    # اگر کاربر contractor است، اجازه تغییر رمز عبور ندارد
    if user.contractor:
        return jsonify({
            "error": "forbidden",
            "message": "تغییر رمز عبور برای پیمانکاران امکان‌پذیر نیست. لطفاً با کارشناس بازرگانی تماس بگیرید."
        }), 403

    payload = request.get_json(silent=True) or {}
    current_password = payload.get("current_password")
    new_password = payload.get("new_password")

    if not current_password or not new_password:
        return jsonify({"error": "missing_credentials"}), 400

    if not user.check_password(current_password):
        return jsonify({"error": "invalid_credentials"}), 401

    user.set_password(new_password)
    user.must_change_password = False
    db.session.commit()

    return jsonify({"status": "password_updated"}), 200

