from __future__ import annotations

from flask import Blueprint, g, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
)

from ..extensions import db
from ..models import Contractor, InvoiceSummary, User
from ..services.audit_log import (
    ACTION_LOGIN,
    ENTITY_USER,
    record_audit,
)
from ..services.import_activation import active_filter
from ..utils.api_errors import error_response
from ..utils.auth_decorators import require_jwt_user
from ..utils.auth_utils import (
    generate_password,
    generate_username,
    generate_username_variants,
    load_authenticated_user,
    normalize_password,
    user_has_staff_access,
)

auth_bp = Blueprint("auth", __name__)


def _find_user_by_username_variants(username: str) -> User | None:
    for variant in generate_username_variants(username):
        user = User.query.filter_by(username=variant).first()
        if user:
            return user
    return None


def _try_lazy_provision_user(username: str, password: str) -> User | None:
    """If no user row matches variants, try contractor match + auto-create user (same as legacy login)."""
    if "_" not in username:
        return None
    username_variants = generate_username_variants(username)
    parts = username.split("_", 1)
    detail_code_search = parts[0].lstrip("0") if parts[0].lstrip("0") else parts[0]
    supplier_code_search = parts[1] if len(parts) > 1 else ""

    contractors = (
        Contractor.query.filter(
            active_filter(Contractor),
            (Contractor.detail_code.like(f"%{detail_code_search}%"))
            & (Contractor.supplier_code.like(f"%{supplier_code_search}%"))
        )
        .limit(3)
        .all()
    )

    if not contractors:
        return None

    contractor = None
    for c in contractors:
        expected_username = generate_username(c)
        if expected_username in username_variants:
            contractor = c
            break

    if not contractor and len(contractors) == 1:
        contractor = contractors[0]

    if not contractor:
        return None

    generated_username = generate_username(contractor)
    generated_password = generate_password(contractor)

    if normalize_password(password) != generated_password:
        return None

    existing_user = User.query.filter_by(username=generated_username).first()
    if existing_user:
        return existing_user

    user = User(
        username=generated_username,
        contractor_id=contractor.id,
        must_change_password=False,
        role="contractor",
    )
    user.set_password(generated_password)
    db.session.add(user)
    db.session.commit()
    return user


def _password_matches_with_legacy_alternates(user: User, password: str) -> bool:
    normalized_password = normalize_password(password)
    if user.check_password(normalized_password):
        return True
    if user.check_password(password):
        return True
    if "@" not in password:
        return False
    parts = password.split("@", 1)
    detail_code = parts[0]
    supplier_code = parts[1] if len(parts) > 1 else ""

    if detail_code and not detail_code.startswith("0"):
        alt_password1 = f"0{detail_code}@{supplier_code}"
        if user.check_password(alt_password1):
            return True

    if supplier_code and not supplier_code.startswith("0"):
        alt_password2 = f"{detail_code}@0{supplier_code}"
        if user.check_password(alt_password2):
            return True

    return False


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username: str | None = payload.get("username")
    password: str | None = payload.get("password")

    if not username or not password:
        return error_response(
            400,
            "missing_credentials",
            "Username and password are required.",
        )

    user = _find_user_by_username_variants(username)
    if user is None:
        user = _try_lazy_provision_user(username, password)

    if user is None:
        return error_response(
            401,
            "invalid_credentials",
            "اطلاعات شما در سیستم یافت نشد. لطفاً با کارشناس بازرگانی تماس بگیرید.",
        )

    if not _password_matches_with_legacy_alternates(user, password):
        return error_response(
            401,
            "invalid_credentials",
            "اطلاعات شما در سیستم یافت نشد. لطفاً با کارشناس بازرگانی تماس بگیرید.",
        )

    contractor: Contractor | None = user.contractor
    if contractor and not contractor.is_active:
        return error_response(
            403,
            "inactive_contractor",
            "Contractor account is inactive.",
        )
    if contractor and contractor.status != "فعال":
        return error_response(
            403,
            "inactive_contractor",
            "حساب کاربری شما غیرفعال است. لطفاً با کارشناس بازرگانی تماس بگیرید.",
        )

    user.last_login_at = db.func.now()
    record_audit(user.id, ACTION_LOGIN, ENTITY_USER, user.id.hex)
    db.session.commit()

    access_token = create_access_token(identity=user.id.hex)
    refresh_token = create_refresh_token(identity=user.id.hex)

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
    user, err = load_authenticated_user()
    if err:
        return err

    access_token = create_access_token(identity=user.id.hex)
    return jsonify({"access_token": access_token}), 200


@auth_bp.get("/me")
@require_jwt_user
def me():
    user = g.current_user

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
        "total_invoices": contractor.invoice_summaries.filter(active_filter(InvoiceSummary)).count(),
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
@require_jwt_user
def change_password():
    """
    تغییر رمز عبور - فقط برای staff/admin users.
    Contractor users نمی‌توانند رمز عبور خود را تغییر دهند.
    """
    user = g.current_user

    if not user_has_staff_access(user):
        return error_response(
            403,
            "forbidden",
            "تغییر رمز عبور برای پیمانکاران امکان‌پذیر نیست. لطفاً با کارشناس بازرگانی تماس بگیرید.",
        )

    payload = request.get_json(silent=True) or {}
    current_password = payload.get("current_password")
    new_password = payload.get("new_password")

    if not current_password or not new_password:
        return error_response(
            400,
            "missing_credentials",
            "Current and new password are required.",
        )

    if not user.check_password(current_password):
        return error_response(
            401,
            "invalid_credentials",
            "Current password is incorrect.",
        )

    user.set_password(new_password)
    user.must_change_password = False
    db.session.commit()

    return jsonify({"status": "password_updated"}), 200
