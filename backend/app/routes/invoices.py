from __future__ import annotations

from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import InvoiceDetail, InvoiceSummary, User

invoices_bp = Blueprint("invoices", __name__)


def _extract_supplier_invoice_numbers(description: str | None) -> list[str]:
    """
    استخراج شماره فاکتورهای تامین‌کننده از فیلد description.
    ممکن است چندین شماره با جداکننده‌های مختلف (کاما، خط جدید، فاصله) جدا شده باشند.
    """
    if not description:
        return []
    
    # حذف فاصله‌های اضافی و تبدیل به یک خط
    text = ' '.join(description.split())
    
    # استخراج شماره‌ها (ممکن است با جداکننده‌های مختلف جدا شده باشند)
    # جداکننده‌ها: کاما، خط جدید، نقطه ویرگول، یا فاصله
    separators = [',', '\n', ';', '،', '|']
    
    # ابتدا با جداکننده‌های مختلف split کنیم
    parts = [text]
    for sep in separators:
        new_parts = []
        for part in parts:
            new_parts.extend(part.split(sep))
        parts = new_parts
    
    # تمیز کردن و فیلتر کردن شماره‌ها
    invoice_numbers = []
    for part in parts:
        # حذف فاصله‌های اضافی
        cleaned = part.strip()
        # اگر خالی نبود و حداقل یک کاراکتر داشت، اضافه کن
        if cleaned and len(cleaned) > 0:
            invoice_numbers.append(cleaned)
    
    # حذف تکراری‌ها و مرتب‌سازی
    return sorted(list(set(invoice_numbers)))


def _get_current_user() -> User | None:
    identity = get_jwt_identity()
    if identity is None:
        return None
    return User.query.get(identity)


@invoices_bp.get("/")
@jwt_required()
def list_invoices():
    user = _get_current_user()
    if not user:
        return jsonify({"error": "not_found"}), 404

    # بررسی اینکه آیا کاربر کارشناس است یا پیمانکار
    is_expert = (hasattr(user, 'role') and user.role == 'expert') or user.username.lower().startswith('admin') or user.username.lower() == 'expert'
    
    if is_expert:
        # کارشناس: همه فاکتورها را می‌بیند
        query = InvoiceSummary.query
    else:
        # پیمانکار: فقط فاکتورهای خودش را می‌بیند
        if not user.contractor:
            return jsonify({"error": "not_found"}), 404
        
        contractor = user.contractor
        # فیلتر بر اساس detail_code و supplier_code (اگر موجود بود)
        query = InvoiceSummary.query.filter_by(detail_code=contractor.detail_code)
        if contractor.supplier_code:
            query = query.filter(
                (InvoiceSummary.supplier_code == contractor.supplier_code) |
                (InvoiceSummary.supplier_code.is_(None))
            )

    status = request.args.getlist("status")
    if status:
        query = query.filter(InvoiceSummary.invoice_status.in_(status))

    cover_number = request.args.get("cover_number")
    if cover_number:
        query = query.filter_by(cover_number=cover_number)

    search = request.args.get("search")
    if search:
        like_term = f"%{search}%"
        query = query.filter(
            InvoiceSummary.cover_number.ilike(like_term)
            | InvoiceSummary.automation_number.ilike(like_term)
            | InvoiceSummary.business_owner.ilike(like_term)
        )

    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(max(int(request.args.get("page_size", 20)), 1), 100)

    pagination = query.order_by(InvoiceSummary.invoice_date.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )

    items = []
    pending_amount = Decimal("0")
    approved_amount = Decimal("0")
    total_invoices = pagination.total

    for summary in pagination.items:
        # دریافت جزئیات برای استخراج شماره فاکتورهای تامین‌کننده
        details_query = InvoiceDetail.query.filter_by(
            cover_number=summary.cover_number, detail_code=summary.detail_code
        )
        if not is_expert and user.contractor and user.contractor.supplier_code:
            details_query = details_query.filter(
                (InvoiceDetail.supplier_code == user.contractor.supplier_code) |
                (InvoiceDetail.supplier_code.is_(None))
            )
        details = details_query.all()
        
        detail_count = len(details)
        
        # استخراج شماره فاکتورهای تامین‌کننده از description
        supplier_invoice_numbers = []
        for detail in details:
            if detail.description:
                extracted = _extract_supplier_invoice_numbers(detail.description)
                supplier_invoice_numbers.extend(extracted)
        
        # حذف تکراری‌ها
        supplier_invoice_numbers = sorted(list(set(supplier_invoice_numbers)))
        supplier_invoice_count = len(supplier_invoice_numbers)

        gross_amount = summary.gross_amount or Decimal("0")
        if summary.invoice_status in {"در انتظار", "جاری", "pending"}:
            pending_amount += gross_amount
        if summary.invoice_status in {"تاييد شده", "تایید شده", "approved"}:
            approved_amount += gross_amount

        items.append(
            {
                "cover_number": summary.cover_number,
                "automation_number": summary.automation_number,
                "invoice_date": summary.invoice_date.isoformat()
                if summary.invoice_date
                else None,
                "invoice_created_at": summary.invoice_created_at.isoformat()
                if summary.invoice_created_at
                else None,
                "delivered_to_supervisor_at": summary.delivered_to_supervisor_at.isoformat()
                if summary.delivered_to_supervisor_at
                else None,
                "delivered_to_accounting_at": summary.delivered_to_accounting_at.isoformat()
                if summary.delivered_to_accounting_at
                else None,
                "status": summary.invoice_status,
                "gross_amount": float(gross_amount),
                "net_amount": float(summary.net_amount or 0),
                "detail_count": detail_count,
                "supplier_invoice_count": supplier_invoice_count,
                "supplier_invoice_numbers": supplier_invoice_numbers,
            }
        )

    return (
        jsonify(
            {
                "page": pagination.page,
                "page_size": pagination.per_page,
                "total": pagination.total,
                "totals": {
                    "total_invoices": total_invoices,
                    "pending_amount": float(pending_amount),
                    "approved_amount": float(approved_amount),
                },
                "items": items,
            }
        ),
        200,
    )


@invoices_bp.get("/<cover_number>")
@jwt_required()
def invoice_detail(cover_number: str):
    user = _get_current_user()
    if not user:
        return jsonify({"error": "not_found"}), 404

    # بررسی اینکه آیا کاربر کارشناس است یا پیمانکار
    is_expert = (hasattr(user, 'role') and user.role == 'expert') or user.username.lower().startswith('admin') or user.username.lower() == 'expert'
    
    if is_expert:
        # کارشناس: همه فاکتورها را می‌بیند
        summary_query = InvoiceSummary.query.filter_by(cover_number=cover_number)
        details_query = InvoiceDetail.query.filter_by(cover_number=cover_number)
    else:
        # پیمانکار: فقط فاکتورهای خودش را می‌بیند
        if not user.contractor:
            return jsonify({"error": "not_found"}), 404
        
        contractor = user.contractor
        summary_query = InvoiceSummary.query.filter_by(
            cover_number=cover_number, detail_code=contractor.detail_code
        )
        if contractor.supplier_code:
            summary_query = summary_query.filter(
                (InvoiceSummary.supplier_code == contractor.supplier_code) |
                (InvoiceSummary.supplier_code.is_(None))
            )
        
        # برای پیمانکار: بر اساس cover_number فیلتر می‌کنیم
        # detail_code ممکن است در InvoiceDetail set نشده باشد (اگر فایل 2 قبل از فایل 1 آپلود شده باشد)
        # پس فقط بر اساس cover_number فیلتر می‌کنیم
        details_query = InvoiceDetail.query.filter_by(cover_number=cover_number)
        
        # اگر supplier_code وجود دارد، فیلتر اضافه می‌کنیم
        if contractor.supplier_code:
            details_query = details_query.filter(
                (InvoiceDetail.supplier_code == contractor.supplier_code) |
                (InvoiceDetail.supplier_code.is_(None))
            )
    
    summary = summary_query.order_by(InvoiceSummary.updated_at.desc()).first()

    if not summary:
        return jsonify({"error": "not_found"}), 404

    detail_rows = []
    all_supplier_invoice_numbers = []
    
    # Log query details for debugging
    print(f"[invoice_detail] Querying InvoiceDetail for cover_number: {cover_number}")
    if not is_expert and user.contractor:
        print(f"[invoice_detail] Contractor: detail_code={user.contractor.detail_code}, supplier_code={user.contractor.supplier_code}")
    
    # Debug: Check all InvoiceDetail records with this cover_number (without filters)
    all_details_debug = InvoiceDetail.query.filter_by(cover_number=cover_number).all()
    print(f"[invoice_detail] DEBUG: Total InvoiceDetail records in DB for cover_number {cover_number}: {len(all_details_debug)}")
    if all_details_debug:
        print(f"[invoice_detail] DEBUG: First record: cover_number={all_details_debug[0].cover_number}, invoice_no={all_details_debug[0].invoice_no}, detail_code={all_details_debug[0].detail_code}, supplier_code={all_details_debug[0].supplier_code}")
    
    details = details_query.order_by(InvoiceDetail.invoice_date.desc()).all()
    print(f"[invoice_detail] Found {len(details)} InvoiceDetail records after filtering for cover_number {cover_number}")
    
    for detail in details:
        # استخراج شماره فاکتور تامین‌کننده از description
        supplier_invoice_numbers = _extract_supplier_invoice_numbers(detail.description)
        all_supplier_invoice_numbers.extend(supplier_invoice_numbers)
        
        detail_rows.append({
            "invoice_no": detail.invoice_no,
            "invoice_date": detail.invoice_date.isoformat()
            if detail.invoice_date
            else None,
            "status": detail.status,
            "item_title": detail.item_title,
            "gross_amount": float(detail.gross_amount or 0),
            "reference": detail.reference,
            "description": detail.description,
            "supplier_name": detail.supplier_name,
            "unit_code": detail.unit_code,
            "supplier_invoice_numbers": supplier_invoice_numbers,
        })
    
    # حذف تکراری‌ها از لیست کلی
    all_supplier_invoice_numbers = sorted(list(set(all_supplier_invoice_numbers)))

    payload = {
        "summary": {
            "cover_number": summary.cover_number,
            "automation_number": summary.automation_number,
            "invoice_status": summary.invoice_status,
            "gross_amount": float(summary.gross_amount or 0),
            "net_amount": float(summary.net_amount or 0),
            "permit_number": summary.permit_number,
            "permit_type": summary.permit_type,
            "client": {
                "name": summary.client_name,
                "contract_number": summary.client_contract_number,
            },
            "dates": {
                "invoice": summary.invoice_date.isoformat()
                if summary.invoice_date
                else None,
                "invoice_created_at": summary.invoice_created_at.isoformat()
                if summary.invoice_created_at
                else None,
                "delivered_to_supervisor_at": summary.delivered_to_supervisor_at.isoformat()
                if summary.delivered_to_supervisor_at
                else None,
                "delivered_to_accounting_at": summary.delivered_to_accounting_at.isoformat()
                if summary.delivered_to_accounting_at
                else None,
                "accounting_document_created_at": summary.invoice_date.isoformat()
                if summary.invoice_date
                else None,
            },
            "notes": summary.notes,
            "supplier_invoice_count": len(all_supplier_invoice_numbers),
            "supplier_invoice_numbers": all_supplier_invoice_numbers,
        },
        "details": detail_rows,
    }

    return jsonify(payload), 200

