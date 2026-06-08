"""
Helper functions for authentication and user management.
"""

from __future__ import annotations

import uuid

from flask_jwt_extended import get_jwt_identity
from sqlalchemy import select

from ..extensions import db
from ..models import User
from .api_errors import error_response

ACTIVE_CONTRACTOR_STATUSES = frozenset(
    {
        "فعال",
        "\u0638\u067e\u0637\xb9\u0637\xa7\u0638\u201e",
        "葳轻",
        "賮毓丕賱",
    }
)


def resolve_user_id(identity) -> uuid.UUID | None:
    """
    Convert JWT identity (hex string or UUID) to a UUID for DB lookups.
    Returns None if the value cannot be parsed.
    """
    if identity is None:
        return None
    if isinstance(identity, uuid.UUID):
        return identity
    if not isinstance(identity, str):
        return None
    s = identity.strip()
    if not s:
        return None
    try:
        return uuid.UUID(s)
    except ValueError:
        pass
    if len(s) == 32:
        try:
            return uuid.UUID(hex=s)
        except ValueError:
            return None
    return None


def user_has_staff_access(user) -> bool:
    """True if the user may access staff/admin API surfaces (invoices-wide, admin blueprint)."""
    if user is None:
        return False
    role = getattr(user, "role", None) or "contractor"
    return role in ("staff", "admin")


def contractor_status_is_active(status: str | None) -> bool:
    """Accept the current Persian value plus legacy mojibake values already present in data/tests."""
    return (status or "").strip() in ACTIVE_CONTRACTOR_STATUSES


def get_jwt_subject_uuid() -> uuid.UUID | None:
    """UUID from the current JWT ``sub`` (identity), or None if missing or unparsable."""
    return resolve_user_id(get_jwt_identity())


def get_current_user() -> User | None:
    """
    Load the User row for the current JWT subject.

    Returns None if the identity cannot be parsed to a UUID, or if no matching user exists.
    Prefer :func:`load_authenticated_user` when you must distinguish invalid token vs missing user.
    """
    uid = get_jwt_subject_uuid()
    if not uid:
        return None
    return load_user_from_database(uid)


def load_user_from_database(uid: uuid.UUID) -> User | None:
    """
    Load the current User row from the database, refreshing any identity-map copy.

    Authorization must not trust a User object that was loaded earlier in the
    same session because role changes must take effect on the next request.
    """
    return db.session.execute(
        select(User)
        .where(User.id == uid)
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()


def load_authenticated_user() -> tuple[User | None, tuple | None]:
    """
    After ``@jwt_required()``: resolve JWT subject to a User.

    Returns ``(user, None)`` on success, or ``(None, error_tuple)`` on failure
    (same shape as :func:`~.api_errors.error_response`: JSON body + status).

    - ``401`` ``invalid_token``: identity missing or not a UUID
    - ``404`` ``not_found``: UUID valid but no user row
    """
    uid = get_jwt_subject_uuid()
    if uid is None:
        return None, error_response(
            401,
            "invalid_token",
            "Invalid or missing user id in token.",
        )
    user = load_user_from_database(uid)
    if user is None:
        return None, error_response(404, "not_found", "User not found.")
    if user.contractor and not user.contractor.is_active:
        return None, error_response(403, "forbidden", "Contractor account is inactive.")
    return user, None


def require_staff_user() -> tuple[User | None, tuple | None]:
    """
    Same as :func:`load_authenticated_user`, then require staff or admin role.

    On missing staff access returns ``403`` ``forbidden`` (user row exists).
    """
    user, err = load_authenticated_user()
    if err is not None:
        return None, err
    if not user_has_staff_access(user):
        return None, error_response(403, "forbidden", "Staff or admin role required.")
    return user, None


def generate_username_variants(username: str) -> list[str]:
    """
    تولید تمام فرمت‌های ممکن username برای جستجو.
    شامل فرمت‌های با و بدون leading zeros.
    
    این تابع برای جستجوی کاربر در دیتابیس استفاده می‌شود تا با هر فرمتی که username ذخیره شده باشد، پیدا شود.
    
    Args:
        username: Username ورودی از کاربر
        
    Returns:
        list[str]: لیست تمام فرمت‌های ممکن username (بدون duplicates، با حفظ ترتیب)
    """
    username = username.strip().lower()
    variants = [username]  # فرمت اصلی
    
    if '_' in username:
        parts = username.split('_', 1)
        detail_code = parts[0]
        supplier_code = parts[1] if len(parts) > 1 else ''
        
        # Normalize supplier_code
        supplier_code_normalized = supplier_code.replace(' ', '').replace('-', '_')
        
        # فرمت نرمالایز شده (بدون leading zeros)
        detail_code_cleaned = detail_code.lstrip('0') if detail_code.lstrip('0') else detail_code
        normalized = f"{detail_code_cleaned}_{supplier_code_normalized}"
        if normalized not in variants:
            variants.append(normalized)
        
        # فرمت‌های با leading zeros (تا 5 leading zero)
        for i in range(1, 6):
            variant = f"{'0' * i}{detail_code_cleaned}_{supplier_code_normalized}"
            if variant not in variants:
                variants.append(variant)
        
        # فرمت اصلی با leading zeros (اگر داشت)
        if detail_code != detail_code_cleaned:
            original_variant = f"{detail_code}_{supplier_code_normalized}"
            if original_variant not in variants:
                variants.append(original_variant)
    else:
        # فقط detail_code
        detail_code_cleaned = username.lstrip('0') if username.lstrip('0') else username
        if detail_code_cleaned not in variants:
            variants.append(detail_code_cleaned)
        
        # فرمت‌های با leading zeros
        for i in range(1, 6):
            variant = f"{'0' * i}{detail_code_cleaned}"
            if variant not in variants:
                variants.append(variant)
    
    # حذف duplicates و برگرداندن (حفظ ترتیب)
    return list(dict.fromkeys(variants))


def normalize_username(username: str) -> str:
    """
    Normalize username برای جستجو در دیتابیس.
    Leading zeros را حذف می‌کند و فرمت را یکسان می‌کند.
    
    این تابع username ورودی را به همان فرمتی تبدیل می‌کند که در generate_username استفاده می‌شود.
    
    Args:
        username: Username ورودی از کاربر
        
    Returns:
        str: Username نرمالایز شده
    """
    username = username.strip().lower()
    
    # اگر username شامل underscore است (فرمت: detail_code_supplier_code)
    if '_' in username:
        parts = username.split('_', 1)
        detail_code = parts[0]
        supplier_code = parts[1] if len(parts) > 1 else ''
        
        # حذف leading zeros از detail_code
        # اگر بعد از حذف leading zeros رشته خالی شد، از خود detail_code استفاده می‌کنیم
        detail_code_cleaned = detail_code.lstrip('0') if detail_code.lstrip('0') else detail_code
        
        if supplier_code:
            # Normalize supplier_code: حذف فاصله و dash، تبدیل به underscore
            supplier_code_normalized = supplier_code.replace(' ', '').replace('-', '_')
            return f"{detail_code_cleaned}_{supplier_code_normalized}"
        else:
            return detail_code_cleaned.replace(' ', '').replace('-', '_')
    else:
        # فقط detail_code (بدون supplier_code)
        # حذف leading zeros
        detail_code_cleaned = username.lstrip('0') if username.lstrip('0') else username
        return detail_code_cleaned.replace(' ', '').replace('-', '_')


def generate_username(contractor) -> str:
    """
    تولید username از detail_code و supplier_code.
    
    فرمت: {detail_code}_{supplier_code} (lowercase, normalized)
    اگر supplier_code خالی بود: فقط detail_code
    
    Args:
        contractor: Contractor model instance
        
    Returns:
        str: Username generated from contractor codes
    """
    detail_code = (contractor.detail_code or "").strip()
    supplier_code = (contractor.supplier_code or "").strip()
    
    # Normalize detail_code: remove leading zeros, lowercase, replace spaces and dashes
    # Leading zeros are removed to match database storage (e.g., "0026968" -> "26968")
    detail_code_cleaned = detail_code.lstrip('0') if detail_code.lstrip('0') else detail_code
    detail_code_normalized = detail_code_cleaned.lower().replace(' ', '').replace('-', '_')
    
    if supplier_code:
        # Normalize supplier_code
        supplier_code_normalized = supplier_code.lower().replace(' ', '').replace('-', '_')
        username = f"{detail_code_normalized}_{supplier_code_normalized}"
    else:
        username = detail_code_normalized
    
    return username


def normalize_password(password: str) -> str:
    """
    Normalize password برای تطابق با password ذخیره شده در دیتابیس.
    Leading zeros را از detail_code در password حذف می‌کند.
    
    فرمت password: {detail_code}@{supplier_code}
    
    این تابع password ورودی را به همان فرمتی تبدیل می‌کند که در generate_password استفاده می‌شود.
    
    Args:
        password: Password ورودی از کاربر
        
    Returns:
        str: Password نرمالایز شده
    """
    password = password.strip()
    
    # اگر password شامل @ است (فرمت: detail_code@supplier_code)
    if '@' in password:
        parts = password.split('@', 1)
        detail_code = parts[0]
        supplier_code = parts[1] if len(parts) > 1 else ''
        
        # حذف leading zeros از detail_code
        # اگر بعد از حذف leading zeros رشته خالی شد، از خود detail_code استفاده می‌کنیم
        detail_code_cleaned = detail_code.lstrip('0') if detail_code.lstrip('0') else detail_code
        
        if supplier_code:
            return f"{detail_code_cleaned}@{supplier_code}"
        else:
            # اگر supplier_code نبود، احتمالاً @2024 یا چیزی شبیه آن است
            return f"{detail_code_cleaned}@2024"
    else:
        # اگر @ نبود، احتمالاً password به فرمت دیگری است
        # در این صورت leading zeros را از کل password حذف می‌کنیم
        return password.lstrip('0') if password.lstrip('0') else password


def generate_password(contractor) -> str:
    """
    تولید password از detail_code و supplier_code.
    
    فرمت: {detail_code}@{supplier_code}
    اگر supplier_code خالی بود: {detail_code}@2024
    
    Args:
        contractor: Contractor model instance
        
    Returns:
        str: Password generated from contractor codes
    """
    detail_code = (contractor.detail_code or "").strip()
    supplier_code = (contractor.supplier_code or "").strip()
    
    # Remove leading zeros from detail_code for password too (to match username)
    detail_code_cleaned = detail_code.lstrip('0') if detail_code.lstrip('0') else detail_code
    
    if supplier_code:
        password = f"{detail_code_cleaned}@{supplier_code}"
    else:
        password = f"{detail_code_cleaned}@2024"
    
    return password

