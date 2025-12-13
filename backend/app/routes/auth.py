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
from ..utils.auth_utils import normalize_username, normalize_password, generate_username_variants

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username: str | None = payload.get("username")
    password: str | None = payload.get("password")

    if not username or not password:
        return jsonify({"error": "missing_credentials"}), 400

    # Debug logging
    print(f"[LOGIN DEBUG] Original username: '{username}'")
    
    # تولید تمام فرمت‌های ممکن username برای جستجو
    username_variants = generate_username_variants(username)
    print(f"[LOGIN DEBUG] Username variants to try: {username_variants[:5]}...")  # فقط 5 تا اول را نمایش بده
    
    # جستجو با تمام فرمت‌های ممکن
    user: User | None = None
    matched_username = None
    
    for variant in username_variants:
        user = User.query.filter_by(username=variant).first()
        if user:
            matched_username = variant
            print(f"[LOGIN DEBUG] User found with username variant: '{variant}'")
            break
    
    if user is None:
        print(f"[LOGIN DEBUG] User not found with any username variant")
        # Try to find similar usernames for debugging
        search_term = username_variants[0].split('_')[0] if '_' in username_variants[0] else username_variants[0]
        similar_users = User.query.filter(User.username.like(f"%{search_term}%")).limit(5).all()
        if similar_users:
            print(f"[LOGIN DEBUG] Found {len(similar_users)} similar usernames:")
            for u in similar_users:
                print(f"[LOGIN DEBUG]   - '{u.username}'")
        
        # Check if contractor exists but user doesn't - auto-create user
        if '_' in username:
            parts = username.split('_', 1)
            detail_code_search = parts[0].lstrip('0') if parts[0].lstrip('0') else parts[0]
            supplier_code_search = parts[1] if len(parts) > 1 else ''
            
            # Try to find contractor
            contractors = Contractor.query.filter(
                (Contractor.detail_code.like(f"%{detail_code_search}%")) &
                (Contractor.supplier_code.like(f"%{supplier_code_search}%"))
            ).limit(3).all()
            
            if contractors:
                print(f"[LOGIN DEBUG] Found {len(contractors)} contractors but no user:")
                from ..utils.auth_utils import generate_username, generate_password
                
                # Try to find exact match contractor
                contractor = None
                for c in contractors:
                    expected_username = generate_username(c)
                    expected_password = generate_password(c)
                    print(f"[LOGIN DEBUG]   - Contractor: detail_code='{c.detail_code}', supplier_code='{c.supplier_code}'")
                    print(f"[LOGIN DEBUG]     Expected username: '{expected_username}'")
                    print(f"[LOGIN DEBUG]     Expected password: '{expected_password}'")
                    
                    # Check if this contractor matches the normalized username
                    if expected_username in username_variants:
                        contractor = c
                        break
                
                # If no exact match, use first contractor
                if not contractor and len(contractors) == 1:
                    contractor = contractors[0]
                
                # Auto-create user if contractor found
                if contractor:
                    generated_username = generate_username(contractor)
                    generated_password = generate_password(contractor)
                    
                    # Verify password matches
                    if normalize_password(password) == generated_password:
                        # Check if username already exists (might be created by another process)
                        existing_user = User.query.filter_by(username=generated_username).first()
                        if existing_user:
                            user = existing_user
                            print(f"[LOGIN DEBUG] User already exists: '{generated_username}'")
                        else:
                            # Create user
                            user = User(
                                username=generated_username,
                                contractor_id=contractor.id,
                                must_change_password=False
                            )
                            user.set_password(generated_password)
                            db.session.add(user)
                            db.session.commit()
                            print(f"[LOGIN DEBUG] Auto-created user: '{generated_username}' for contractor '{contractor.detail_code}_{contractor.supplier_code}'")
        
        if user is None:
            return jsonify({
                "error": "not_found",
                "message": "اطلاعات شما در سیستم یافت نشد. لطفاً با کارشناس بازرگانی تماس بگیرید."
            }), 401
    
    print(f"[LOGIN DEBUG] User found: '{user.username}'")
    if user.contractor:
        print(f"[LOGIN DEBUG] Contractor: detail_code='{user.contractor.detail_code}', supplier_code='{user.contractor.supplier_code}'")
    
    # Normalize password قبل از بررسی (حذف leading zeros از detail_code در password)
    normalized_password = normalize_password(password)
    
    print(f"[LOGIN DEBUG] Original password: '{password}'")
    print(f"[LOGIN DEBUG] Normalized password: '{normalized_password}'")
    
    password_check_result = user.check_password(normalized_password)
    print(f"[LOGIN DEBUG] Password check result: {password_check_result}")
    
    # Fallback: اگر password check ناموفق بود، با فرمت‌های مختلف امتحان کنیم
    if not password_check_result:
        # Try with original password
        original_check = user.check_password(password)
        print(f"[LOGIN DEBUG] Password check with original: {original_check}")
        
        if not original_check and '@' in password:
            # Try alternative password formats
            parts = password.split('@', 1)
            detail_code = parts[0]
            supplier_code = parts[1] if len(parts) > 1 else ''
            
            # Try with leading zeros in detail_code
            if detail_code and not detail_code.startswith('0'):
                alt_password1 = f"0{detail_code}@{supplier_code}"
                print(f"[LOGIN DEBUG] Trying alternative password: '{alt_password1}'")
                if user.check_password(alt_password1):
                    password_check_result = True
                    print(f"[LOGIN DEBUG] Password match found with alternative format")
            
            # Try with leading zeros in supplier_code
            if not password_check_result and supplier_code and not supplier_code.startswith('0'):
                alt_password2 = f"{detail_code}@0{supplier_code}"
                print(f"[LOGIN DEBUG] Trying alternative password: '{alt_password2}'")
                if user.check_password(alt_password2):
                    password_check_result = True
                    print(f"[LOGIN DEBUG] Password match found with alternative format")
        
        if not password_check_result:
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


@auth_bp.get("/debug/check-user")
def debug_check_user():
    """
    Endpoint تست برای بررسی وجود کاربر و contractor
    Query params: username (مثلاً 71499_726)
    """
    username = request.args.get("username", "")
    if not username:
        return jsonify({"error": "username_required"}), 400
    
    from ..utils.auth_utils import generate_username_variants, generate_username, generate_password
    
    username_variants = generate_username_variants(username)
    found_users = []
    
    for variant in username_variants:
        user = User.query.filter_by(username=variant).first()
        if user:
            found_users.append({
                "username": user.username,
                "contractor_id": str(user.contractor_id) if user.contractor_id else None,
                "contractor": {
                    "detail_code": user.contractor.detail_code,
                    "supplier_code": user.contractor.supplier_code,
                } if user.contractor else None,
            })
    
    # Check contractor
    contractors_found = []
    if '_' in username:
        parts = username.split('_', 1)
        detail_code_search = parts[0].lstrip('0') if parts[0].lstrip('0') else parts[0]
        supplier_code_search = parts[1] if len(parts) > 1 else ''
        
        contractors = Contractor.query.filter(
            (Contractor.detail_code.like(f"%{detail_code_search}%")) &
            (Contractor.supplier_code.like(f"%{supplier_code_search}%"))
        ).limit(5).all()
        
        for c in contractors:
            expected_username = generate_username(c)
            expected_password = generate_password(c)
            has_user = User.query.filter_by(contractor_id=c.id).first() is not None
            contractors_found.append({
                "detail_code": c.detail_code,
                "supplier_code": c.supplier_code,
                "expected_username": expected_username,
                "expected_password": expected_password,
                "has_user": has_user,
            })
    
    return jsonify({
        "input_username": username,
        "username_variants_tried": username_variants[:10],  # فقط 10 تا اول
        "users_found": found_users,
        "contractors_found": contractors_found,
    }), 200


@auth_bp.post("/debug/create-user")
def debug_create_user():
    """
    Endpoint تست برای ساخت خودکار user برای contractor (فقط برای توسعه)
    Body: {"username": "71499_726"}
    """
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "")
    
    if not username:
        return jsonify({"error": "username_required"}), 400
    
    from ..utils.auth_utils import generate_username, generate_password, generate_username_variants
    
    # Find contractor
    if '_' not in username:
        return jsonify({"error": "invalid_username_format"}), 400
    
    parts = username.split('_', 1)
    detail_code_search = parts[0].lstrip('0') if parts[0].lstrip('0') else parts[0]
    supplier_code_search = parts[1] if len(parts) > 1 else ''
    
    contractor = Contractor.query.filter(
        (Contractor.detail_code.like(f"%{detail_code_search}%")) &
        (Contractor.supplier_code.like(f"%{supplier_code_search}%"))
    ).first()
    
    if not contractor:
        return jsonify({"error": "contractor_not_found"}), 404
    
    # Check if user already exists
    existing_user = User.query.filter_by(contractor_id=contractor.id).first()
    if existing_user:
        return jsonify({
            "error": "user_exists",
            "username": existing_user.username,
            "message": "کاربری برای این پیمانکار از قبل وجود دارد."
        }), 400
    
    # Generate username and password
    generated_username = generate_username(contractor)
    generated_password = generate_password(contractor)
    
    # Check if username already exists
    if User.query.filter_by(username=generated_username).first():
        return jsonify({
            "error": "username_exists",
            "message": f"نام کاربری '{generated_username}' از قبل وجود دارد."
        }), 400
    
    # Create user
    user = User(
        username=generated_username,
        contractor_id=contractor.id,
        must_change_password=False
    )
    user.set_password(generated_password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "username": generated_username,
        "password": generated_password,
        "contractor": {
            "detail_code": contractor.detail_code,
            "supplier_code": contractor.supplier_code,
        },
        "message": "User created successfully"
    }), 200


@auth_bp.post("/debug/create-missing-users")
def debug_create_missing_users():
    """
    Endpoint تست برای ساخت خودکار user برای تمام contractorهایی که user ندارند
    """
    from ..utils.auth_utils import generate_username, generate_password
    
    # Find all contractors without users
    contractors_without_users = db.session.query(Contractor).outerjoin(
        User, Contractor.id == User.contractor_id
    ).filter(User.id == None).all()
    
    created_users = []
    errors = []
    
    for contractor in contractors_without_users:
        try:
            # Generate username and password
            generated_username = generate_username(contractor)
            generated_password = generate_password(contractor)
            
            # Check if username already exists
            if User.query.filter_by(username=generated_username).first():
                errors.append({
                    "contractor_id": str(contractor.id),
                    "detail_code": contractor.detail_code,
                    "supplier_code": contractor.supplier_code,
                    "error": "username_exists",
                    "username": generated_username,
                })
                continue
            
            # Create user
            user = User(
                username=generated_username,
                contractor_id=contractor.id,
                must_change_password=False
            )
            user.set_password(generated_password)
            db.session.add(user)
            
            created_users.append({
                "username": generated_username,
                "password": generated_password,
                "contractor": {
                    "detail_code": contractor.detail_code,
                    "supplier_code": contractor.supplier_code,
                },
            })
        except Exception as e:
            errors.append({
                "contractor_id": str(contractor.id),
                "detail_code": contractor.detail_code,
                "supplier_code": contractor.supplier_code,
                "error": str(e),
            })
    
    # Commit all at once
    if created_users:
        db.session.commit()
    
    return jsonify({
        "success": True,
        "created_count": len(created_users),
        "error_count": len(errors),
        "created_users": created_users[:20],  # فقط 20 تا اول را برگردان
        "errors": errors[:20],  # فقط 20 تا اول را برگردان
        "message": f"Created {len(created_users)} users, {len(errors)} errors"
    }), 200

