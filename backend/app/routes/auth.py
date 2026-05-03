from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)

from ..extensions import db
from ..models import Contractor, User
from ..utils.auth_utils import (
    generate_password,
    generate_username,
    generate_username_variants,
    normalize_password,
    resolve_user_id,
)

auth_bp = Blueprint("auth", __name__)


def _jwt_claims(user: User) -> dict:
    return {"role": user.role}


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username: str | None = payload.get("username")
    password: str | None = payload.get("password")

    if not username or not password:
        return jsonify({"error": "missing_credentials"}), 400

    username_variants = generate_username_variants(username)

    user: User | None = None
    for variant in username_variants:
        user = User.query.filter_by(username=variant).first()
        if user:
            break

    if user is None:
        if "_" in username:
            parts = username.split("_", 1)
            detail_code_search = parts[0].lstrip("0") if parts[0].lstrip("0") else parts[0]
            supplier_code_search = parts[1] if len(parts) > 1 else ""

            contractors = (
                Contractor.query.filter(
                    (Contractor.detail_code.like(f"%{detail_code_search}%"))
                    & (Contractor.supplier_code.like(f"%{supplier_code_search}%"))
                )
                .limit(3)
                .all()
            )

            if contractors:
                contractor = None
                for c in contractors:
                    expected_username = generate_username(c)
                    if expected_username in username_variants:
                        contractor = c
                        break

                if not contractor and len(contractors) == 1:
                    contractor = contractors[0]

                if contractor:
                    generated_username = generate_username(contractor)
                    generated_password = generate_password(contractor)

                    if normalize_password(password) == generated_password:
                        existing_user = User.query.filter_by(username=generated_username).first()
                        if existing_user:
                            user = existing_user
                        else:
                            user = User(
                                username=generated_username,
                                contractor_id=contractor.id,
                                must_change_password=False,
                                role="contractor",
                            )
                            user.set_password(generated_password)
                            db.session.add(user)
                            db.session.commit()

        if user is None:
            return jsonify(
                {
                    "error": "not_found",
                    "message": "اطلاعات شما در سیستم یافت نشد. لطفاً با کارشناس بازرگانی تماس بگیرید.",
                }
            ), 401

    normalized_password = normalize_password(password)

    password_check_result = user.check_password(normalized_password)

    if not password_check_result:
        original_check = user.check_password(password)
        if not original_check and "@" in password:
            parts = password.split("@", 1)
            detail_code = parts[0]
            supplier_code = parts[1] if len(parts) > 1 else ""

            if detail_code and not detail_code.startswith("0"):
                alt_password1 = f"0{detail_code}@{supplier_code}"
                if user.check_password(alt_password1):
                    password_check_result = True

            if not password_check_result and supplier_code and not supplier_code.startswith("0"):
                alt_password2 = f"{detail_code}@0{supplier_code}"
                if user.check_password(alt_password2):
                    password_check_result = True

        if not password_check_result:
            return jsonify(
                {
                    "error": "invalid_credentials",
                    "message": "اطلاعات شما در سیستم یافت نشد. لطفاً با کارشناس بازرگانی تماس بگیرید.",
                }
            ), 401

    contractor: Contractor | None = user.contractor
    if contractor and contractor.status != "فعال":
        return jsonify(
            {
                "error": "inactive_contractor",
                "message": "حساب کاربری شما غیرفعال است. لطفاً با کارشناس بازرگانی تماس بگیرید.",
            }
        ), 403

    user.last_login_at = db.func.now()
    db.session.commit()

    claims = _jwt_claims(user)
    access_token = create_access_token(identity=user.id.hex, additional_claims=claims)
    refresh_token = create_refresh_token(identity=user.id.hex, additional_claims=claims)

    response_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "must_change_password": user.must_change_password,
    }

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
    user_id = resolve_user_id(identity)
    if not user_id:
        return jsonify({"error": "invalid_token"}), 401
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "not_found"}), 401

    access_token = create_access_token(
        identity=user.id.hex,
        additional_claims=_jwt_claims(user),
    )
    return jsonify({"access_token": access_token}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    identity = get_jwt_identity()
    user_id = resolve_user_id(identity)
    if not user_id:
        return jsonify({"error": "invalid_token"}), 401

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "not_found"}), 404

    if not user.contractor:
        return (
            jsonify(
                {
                    "user": {
                        "username": user.username,
                        "last_login_at": user.last_login_at,
                        "role": user.role,
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
                    "role": user.role,
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
    تغییر رمز عبور - فقط برای staff/admin users.
    Contractor users نمی‌توانند رمز عبور خود را تغییر دهند.
    """
    identity = get_jwt_identity()
    user_id = resolve_user_id(identity)
    if not user_id:
        return jsonify({"error": "invalid_token"}), 401
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "not_found"}), 404

    if user.role == "contractor":
        return jsonify(
            {
                "error": "forbidden",
                "message": "تغییر رمز عبور برای پیمانکاران امکان‌پذیر نیست. لطفاً با کارشناس بازرگانی تماس بگیرید.",
            }
        ), 403

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
