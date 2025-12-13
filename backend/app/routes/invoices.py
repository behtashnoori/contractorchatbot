from __future__ import annotations

from decimal import Decimal
from datetime import datetime, date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import extract, func, case, distinct, or_, select
from convertdate import persian

from ..models import InvoiceDetail, InvoiceSummary, User

invoices_bp = Blueprint("invoices", __name__)


def get_persian_fiscal_year(gregorian_date: date | None) -> int | None:
    """
    تبدیل تاریخ میلادی به سال مالی شمسی
    سال مالی شمسی: از 1 فروردین (تقریباً 21 مارس) شروع می‌شود
    """
    if not gregorian_date:
        return None
    p_year, p_month, p_day = persian.from_gregorian(
        gregorian_date.year, 
        gregorian_date.month, 
        gregorian_date.day
    )
    return p_year


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
        
        # استفاده از همان منطق fallback که در filters/options استفاده می‌شود
        # ساخت query با استفاده از or_ برای ترکیب شرط‌ها
        # شرط 1: detail_code match
        # شرط 2: cover_number از InvoiceDetail (fallback)
        conditions = []
        
        # شرط اصلی: detail_code برابر
        detail_code_condition = InvoiceSummary.detail_code == contractor.detail_code
        conditions.append(detail_code_condition)
        
        # Fallback: اگر supplier_code موجود است، cover_number های مربوط به این contractor از InvoiceDetail را هم در نظر می‌گیریم
        # اما فقط summaries با cover_number در لیست که detail_code این contractor نیست (تا تکراری نشوند)
        # بهینه‌سازی: استفاده از subquery به جای separate query
        if contractor.supplier_code:
            # استفاده از subquery برای بهینه‌سازی
            matching_cover_numbers_subquery = select(distinct(InvoiceDetail.cover_number)).where(
                (InvoiceDetail.supplier_code == contractor.supplier_code) |
                (InvoiceDetail.supplier_code.is_(None))
            ).scalar_subquery()
            
            # شرط fallback: cover_number در subquery است اما detail_code این contractor نیست
            # (تا summaries با detail_code این contractor که قبلاً در شرط اصلی هستند، تکراری نشوند)
            fallback_condition = (
                InvoiceSummary.cover_number.in_(matching_cover_numbers_subquery) &
                (InvoiceSummary.detail_code != contractor.detail_code)
            )
            conditions.append(fallback_condition)
            
            # Debug: تعداد cover_numbers (فقط برای logging)
            matching_details_count = InvoiceDetail.query.filter(
                (InvoiceDetail.supplier_code == contractor.supplier_code) |
                (InvoiceDetail.supplier_code.is_(None))
            ).with_entities(distinct(InvoiceDetail.cover_number)).count()
            print(f"[LIST_INVOICES DEBUG] Found {matching_details_count} unique cover_numbers from InvoiceDetail (using subquery)")
        
        # ترکیب شرط‌ها با or_
        if len(conditions) > 1:
            query = InvoiceSummary.query.filter(or_(*conditions))
        else:
            query = InvoiceSummary.query.filter(conditions[0])
        
        # اعمال فیلتر supplier_code (اگر موجود بود)
        if contractor.supplier_code:
            query = query.filter(
                (InvoiceSummary.supplier_code == contractor.supplier_code) |
                (InvoiceSummary.supplier_code.is_(None))
            )
    
    # Debug: تعداد اولیه summaries
    initial_count = query.count()
    print(f"[LIST_INVOICES] Initial summaries count (after contractor filter with fallback): {initial_count}")

    # فیلتر وضعیت: پشتیبانی از هم string و هم array
    status = request.args.getlist("status")
    if not status:
        # اگر getlist چیزی برنگرداند، get را امتحان کنیم (برای string)
        status_str = request.args.get("status")
        if status_str:
            status = [status_str]
    
    if status:
        print(f"[LIST_INVOICES DEBUG] Filtering by status: {status}")
        # Debug: بررسی summaries قبل از فیلتر status
        summaries_before_status = query.all()
        statuses_before = set([s.invoice_status for s in summaries_before_status if s.invoice_status])
        print(f"[LIST_INVOICES DEBUG] Statuses before filter: {statuses_before}")
        print(f"[LIST_INVOICES DEBUG] Count of summaries before status filter: {len(summaries_before_status)}")
        # بررسی تعداد summaries با status مورد نظر قبل از فیلتر
        for status_val in status:
            count_before = sum([1 for s in summaries_before_status if s.invoice_status == status_val])
            print(f"[LIST_INVOICES DEBUG] Count of '{status_val}' before filter: {count_before}")
        
        query = query.filter(InvoiceSummary.invoice_status.in_(status))
        # Debug: تعداد summaries بعد از فیلتر وضعیت
        count_after_status = query.count()
        print(f"[LIST_INVOICES DEBUG] Summaries after status filter: {count_after_status}")
        
        # Debug: بررسی summaries بعد از فیلتر
        summaries_after_status = query.all()
        statuses_after = set([s.invoice_status for s in summaries_after_status if s.invoice_status])
        print(f"[LIST_INVOICES DEBUG] Statuses after filter: {statuses_after}")
        print(f"[LIST_INVOICES DEBUG] Cover numbers after status filter: {[s.cover_number for s in summaries_after_status[:10]]}")

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
    
    # فیلتر بر اساس سال مالی شمسی
    # سال مالی شمسی: از 1 فروردین شروع می‌شود
    fiscal_year = request.args.get("fiscal_year")
    if fiscal_year:
        try:
            fiscal_year_int = int(fiscal_year)
            print(f"[LIST_INVOICES DEBUG] Filtering by fiscal year: {fiscal_year_int}")
            
            # تبدیل 1 فروردین fiscal_year به میلادی
            g_year_start, g_month_start, g_day_start = persian.to_gregorian(fiscal_year_int, 1, 1)
            print(f"[LIST_INVOICES DEBUG] Start date (Gregorian): {g_year_start}-{g_month_start:02d}-{g_day_start:02d}")
            
            # تبدیل آخرین روز اسفند fiscal_year به میلادی
            # ابتدا 29 اسفند را امتحان می‌کنیم (سال غیر کبیسه)
            try:
                g_year_end, g_month_end, g_day_end = persian.to_gregorian(fiscal_year_int, 12, 29)
                # اگر 30 اسفند وجود داشت، از آن استفاده می‌کنیم
                try:
                    g_year_end_30, g_month_end_30, g_day_end_30 = persian.to_gregorian(fiscal_year_int, 12, 30)
                    g_year_end, g_month_end, g_day_end = g_year_end_30, g_month_end_30, g_day_end_30
                    print(f"[LIST_INVOICES DEBUG] Using 30 Esfand (leap year)")
                except (ValueError, OverflowError):
                    print(f"[LIST_INVOICES DEBUG] Using 29 Esfand (non-leap year)")
            except (ValueError, OverflowError):
                # اگر 29 اسفند هم وجود نداشت (که نباید اتفاق بیفتد)
                g_year_end, g_month_end, g_day_end = persian.to_gregorian(fiscal_year_int, 12, 28)
                print(f"[LIST_INVOICES DEBUG] Using 28 Esfand (fallback)")
            
            print(f"[LIST_INVOICES DEBUG] End date (Gregorian): {g_year_end}-{g_month_end:02d}-{g_day_end:02d}")
            
            start_date = date(g_year_start, g_month_start, g_day_start)
            end_date = date(g_year_end, g_month_end, g_day_end)
            
            print(f"[LIST_INVOICES DEBUG] Filtering: invoice_created_at >= {start_date} AND invoice_created_at <= {end_date}")
            
            # Debug: تعداد summaries قبل از فیلتر سال مالی
            count_before_fiscal = query.count()
            print(f"[LIST_INVOICES DEBUG] Summaries before fiscal year filter: {count_before_fiscal}")
            
            query = query.filter(
                InvoiceSummary.invoice_created_at >= start_date,
                InvoiceSummary.invoice_created_at <= end_date
            )
            
            # Debug: تعداد summaries بعد از فیلتر سال مالی
            count_after_fiscal = query.count()
            print(f"[LIST_INVOICES DEBUG] Summaries after fiscal year filter: {count_after_fiscal}")
            
        except (ValueError, TypeError, OverflowError) as e:
            print(f"[LIST_INVOICES DEBUG] Error in fiscal year filter: {e}")
            pass  # Invalid fiscal_year, ignore

    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(max(int(request.args.get("page_size", 20)), 1), 100)

    # Debug: تعداد نهایی summaries قبل از pagination
    final_count = query.count()
    print(f"[LIST_INVOICES DEBUG] Final summaries count before pagination: {final_count}")

    pagination = query.order_by(InvoiceSummary.invoice_created_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )
    
    print(f"[LIST_INVOICES DEBUG] Pagination: page={pagination.page}, per_page={pagination.per_page}, total={pagination.total}, items={len(pagination.items)}")

    items = []
    pending_amount = Decimal("0")
    approved_amount = Decimal("0")
    total_invoices = pagination.total

    # بهینه‌سازی: یک query برای همه details به جای N+1 queries
    cover_numbers = [s.cover_number for s in pagination.items]
    detail_codes = list(set([s.detail_code for s in pagination.items if s.detail_code]))
    
    # یک query برای همه details مربوط به summaries در این صفحه
    all_details_query = InvoiceDetail.query.filter(
        InvoiceDetail.cover_number.in_(cover_numbers)
    )
    if detail_codes:
        all_details_query = all_details_query.filter(InvoiceDetail.detail_code.in_(detail_codes))
    
    if not is_expert and user.contractor and user.contractor.supplier_code:
        all_details_query = all_details_query.filter(
            (InvoiceDetail.supplier_code == user.contractor.supplier_code) |
            (InvoiceDetail.supplier_code.is_(None))
        )
    
    all_details = all_details_query.all()
    
    # Group details by (cover_number, detail_code)
    details_by_cover = {}
    for detail in all_details:
        key = (detail.cover_number, detail.detail_code)
        if key not in details_by_cover:
            details_by_cover[key] = []
        details_by_cover[key].append(detail)

    for summary in pagination.items:
        # استفاده از details از cache
        key = (summary.cover_number, summary.detail_code)
        details = details_by_cover.get(key, [])
        
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

        # محاسبه سال مالی شمسی از تاریخ ایجاد فاکتور
        fiscal_year = get_persian_fiscal_year(summary.invoice_created_at)

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
                "fiscal_year": fiscal_year,
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
        summary = summary_query.order_by(InvoiceSummary.updated_at.desc()).first()
    else:
        # پیمانکار: فقط فاکتورهای خودش را می‌بیند
        if not user.contractor:
            return jsonify({"error": "not_found"}), 404
        
        contractor = user.contractor
        print(f"[invoice_detail] Contractor: detail_code='{contractor.detail_code}', supplier_code='{contractor.supplier_code}'")
        
        # ابتدا سعی می‌کنیم با detail_code پیدا کنیم
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
        
        # اگر summary پیدا نشد، بررسی می‌کنیم که آیا invoice با cover_number وجود دارد اما detail_code match نمی‌کند
        # در این صورت، اگر InvoiceDetail با cover_number و supplier_code match پیدا کردیم، summary را بدون detail_code filter می‌گیریم
        summary = summary_query.order_by(InvoiceSummary.updated_at.desc()).first()
        if not summary:
            # Check if any invoice with this cover_number exists
            any_summary = InvoiceSummary.query.filter_by(cover_number=cover_number).first()
            if any_summary:
                print(f"[invoice_detail] InvoiceSummary found but detail_code doesn't match")
                print(f"[invoice_detail] Invoice detail_code: '{any_summary.detail_code}', supplier_code: '{any_summary.supplier_code}'")
                
                # Check if InvoiceDetail exists with matching supplier_code
                test_details = InvoiceDetail.query.filter_by(cover_number=cover_number)
                if contractor.supplier_code:
                    test_details = test_details.filter(
                        (InvoiceDetail.supplier_code == contractor.supplier_code) |
                        (InvoiceDetail.supplier_code.is_(None))
                    )
                matching_details = test_details.first()
                
                if matching_details:
                    print(f"[invoice_detail] Found matching InvoiceDetail, using summary without detail_code filter")
                    print(f"[invoice_detail] Matching detail: detail_code='{matching_details.detail_code}', supplier_code='{matching_details.supplier_code}'")
                    # Use summary without detail_code filter
                    # اگر InvoiceDetail با supplier_code match کرد، summary را بدون فیلتر detail_code می‌گیریم
                    fallback_summary_query = InvoiceSummary.query.filter_by(cover_number=cover_number)
                    if contractor.supplier_code:
                        fallback_summary_query = fallback_summary_query.filter(
                            (InvoiceSummary.supplier_code == contractor.supplier_code) |
                            (InvoiceSummary.supplier_code.is_(None))
                        )
                    summary = fallback_summary_query.order_by(InvoiceSummary.updated_at.desc()).first()
                    if summary:
                        print(f"[invoice_detail] Found summary with fallback: detail_code='{summary.detail_code}', supplier_code='{summary.supplier_code}'")
                    else:
                        print(f"[invoice_detail] No summary found even with fallback (supplier_code filter)")
                        # اگر با supplier_code filter هم پیدا نشد، بدون هیچ فیلتری امتحان می‌کنیم
                        summary = InvoiceSummary.query.filter_by(cover_number=cover_number).order_by(InvoiceSummary.updated_at.desc()).first()
                        if summary:
                            print(f"[invoice_detail] Found summary without any filter: detail_code='{summary.detail_code}', supplier_code='{summary.supplier_code}'")

    if not summary:
        # Debug: Check if invoice exists but filtered out
        any_summary = InvoiceSummary.query.filter_by(cover_number=cover_number).first()
        if any_summary:
            print(f"[invoice_detail] Invoice exists with cover_number {cover_number} but filtered out")
            print(f"[invoice_detail] Invoice detail_code: '{any_summary.detail_code}', supplier_code: '{any_summary.supplier_code}'")
            if not is_expert and user.contractor:
                print(f"[invoice_detail] Contractor detail_code: '{user.contractor.detail_code}', supplier_code: '{user.contractor.supplier_code}'")
        else:
            print(f"[invoice_detail] No invoice found with cover_number {cover_number}")
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

    # محاسبه سال مالی شمسی از تاریخ ایجاد فاکتور
    fiscal_year = get_persian_fiscal_year(summary.invoice_created_at)

    payload = {
        "summary": {
            "cover_number": summary.cover_number,
            "automation_number": summary.automation_number,
            "invoice_status": summary.invoice_status,
            "gross_amount": float(summary.gross_amount or 0),
            "net_amount": float(summary.net_amount or 0),
            "permit_number": summary.permit_number,
            "permit_type": summary.permit_type,
            "cost_subject": summary.cost_subject,
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
                "accounting_document_created_at": summary.delivered_to_accounting_at.isoformat()
                if summary.delivered_to_accounting_at
                else None,
            },
            "notes": summary.notes,
            "supplier_invoice_count": len(all_supplier_invoice_numbers),
            "supplier_invoice_numbers": all_supplier_invoice_numbers,
            "fiscal_year": fiscal_year,
        },
        "details": detail_rows,
    }

    return jsonify(payload), 200


@invoices_bp.get("/debug/check-invoice")
@jwt_required()
def debug_check_invoice():
    """
    Endpoint دیباگ برای بررسی وجود invoice و فیلترها
    Query params: cover_number (مثلاً 14032237)
    """
    cover_number = request.args.get("cover_number", "")
    if not cover_number:
        return jsonify({"error": "cover_number_required"}), 400
    
    user = _get_current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    
    is_expert = (hasattr(user, 'role') and user.role == 'expert') or user.username.lower().startswith('admin') or user.username.lower() == 'expert'
    
    # Check if invoice exists
    any_summary = InvoiceSummary.query.filter_by(cover_number=cover_number).first()
    any_details = InvoiceDetail.query.filter_by(cover_number=cover_number).all()
    
    result = {
        "cover_number": cover_number,
        "invoice_summary_exists": any_summary is not None,
        "invoice_details_count": len(any_details),
    }
    
    if any_summary:
        result["summary"] = {
            "detail_code": any_summary.detail_code,
            "supplier_code": any_summary.supplier_code,
        }
    
    if any_details:
        result["details"] = [{
            "detail_code": d.detail_code,
            "supplier_code": d.supplier_code,
            "invoice_no": d.invoice_no,
        } for d in any_details[:10]]  # فقط 10 تا اول
    
    if not is_expert and user.contractor:
        contractor = user.contractor
        result["contractor"] = {
            "detail_code": contractor.detail_code,
            "supplier_code": contractor.supplier_code,
        }
        
        # Check if would be filtered
        if any_summary:
            detail_code_match = any_summary.detail_code == contractor.detail_code
            supplier_code_match = (
                not contractor.supplier_code or
                any_summary.supplier_code == contractor.supplier_code or
                any_summary.supplier_code is None
            )
            result["summary_would_match"] = detail_code_match and supplier_code_match
            result["summary_detail_code_match"] = detail_code_match
            result["summary_supplier_code_match"] = supplier_code_match
        
        # Check InvoiceDetail matches
        if any_details:
            matching_details = []
            for d in any_details:
                detail_match = (
                    not contractor.supplier_code or
                    d.supplier_code == contractor.supplier_code or
                    d.supplier_code is None
                )
                if detail_match:
                    matching_details.append({
                        "detail_code": d.detail_code,
                        "supplier_code": d.supplier_code,
                        "invoice_no": d.invoice_no,
                    })
            result["matching_details"] = matching_details
            result["has_matching_details"] = len(matching_details) > 0
    
    return jsonify(result), 200


@invoices_bp.get("/filters/options")
@jwt_required()
def get_filter_options():
    """
    دریافت لیست سال‌های مالی و وضعیت‌های موجود برای فیلتر
    """
    user = _get_current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    
    is_expert = (hasattr(user, 'role') and user.role == 'expert') or user.username.lower().startswith('admin') or user.username.lower() == 'expert'
    
    # ساخت query اولیه بر اساس contractor
    # استفاده از منطق مشابه endpoint اصلی با fallback logic
    if is_expert:
        base_query = InvoiceSummary.query
    else:
        if not user.contractor:
            return jsonify({"error": "not_found"}), 404
        contractor = user.contractor
        
        # Debug: بررسی تعداد summaries قبل از فیلتر
        total_before_filter = InvoiceSummary.query.count()
        print(f"[FILTERS/OPTIONS DEBUG] Total summaries in DB: {total_before_filter}")
        
        # ساخت query با استفاده از or_ برای ترکیب شرط‌ها
        # شرط 1: detail_code match
        # شرط 2: cover_number از InvoiceDetail (fallback)
        conditions = []
        
        # شرط اصلی: detail_code برابر
        detail_code_condition = InvoiceSummary.detail_code == contractor.detail_code
        conditions.append(detail_code_condition)
        
        # Fallback: اگر supplier_code موجود است، cover_number های مربوط به این contractor از InvoiceDetail را هم در نظر می‌گیریم
        # اما فقط summaries با cover_number در لیست که detail_code این contractor نیست (تا تکراری نشوند)
        # بهینه‌سازی: استفاده از subquery به جای separate query
        if contractor.supplier_code:
            # استفاده از subquery برای بهینه‌سازی
            matching_cover_numbers_subquery = select(distinct(InvoiceDetail.cover_number)).where(
                (InvoiceDetail.supplier_code == contractor.supplier_code) |
                (InvoiceDetail.supplier_code.is_(None))
            ).scalar_subquery()
            
            # شرط fallback: cover_number در subquery است اما detail_code این contractor نیست
            # (تا summaries با detail_code این contractor که قبلاً در شرط اصلی هستند، تکراری نشوند)
            fallback_condition = (
                InvoiceSummary.cover_number.in_(matching_cover_numbers_subquery) &
                (InvoiceSummary.detail_code != contractor.detail_code)
            )
            conditions.append(fallback_condition)
            
            # Debug: تعداد cover_numbers (فقط برای logging)
            matching_details_count = InvoiceDetail.query.filter(
                (InvoiceDetail.supplier_code == contractor.supplier_code) |
                (InvoiceDetail.supplier_code.is_(None))
            ).with_entities(distinct(InvoiceDetail.cover_number)).count()
            print(f"[FILTERS/OPTIONS DEBUG] Found {matching_details_count} unique cover_numbers from InvoiceDetail (using subquery)")
        
        # ترکیب شرط‌ها با or_
        if len(conditions) > 1:
            base_query = InvoiceSummary.query.filter(or_(*conditions))
        else:
            base_query = InvoiceSummary.query.filter(conditions[0])
        
        # اعمال فیلتر supplier_code (اگر موجود بود)
        if contractor.supplier_code:
            base_query = base_query.filter(
                (InvoiceSummary.supplier_code == contractor.supplier_code) |
                (InvoiceSummary.supplier_code.is_(None))
            )
        
        # Debug: بررسی تعداد summaries
        count_after_filter = base_query.count()
        print(f"[FILTERS/OPTIONS DEBUG] Summaries after filter: {count_after_filter}")
    
    # دریافت فیلترها از query params
    fiscal_year_filter = request.args.get("fiscal_year")
    status_filter = request.args.get("status")  # برای فیلتر کردن سال‌های مالی
    
    print(f"[FILTERS/OPTIONS] Received filters: fiscal_year={fiscal_year_filter}, status={status_filter}")
    
    # برای استخراج سال‌های مالی: اعمال فیلتر وضعیت (اگر موجود باشد)
    # حالا می‌توانیم همزمان از هر دو فیلتر استفاده کنیم
    fiscal_year_query = base_query
    if status_filter:
        fiscal_year_query = fiscal_year_query.filter(InvoiceSummary.invoice_status == status_filter)
        print(f"[FILTERS/OPTIONS] Filtering fiscal years by status: {status_filter}")
    
    # اگر فیلتر سال مالی موجود باشد، آن را اعمال می‌کنیم (برای نمایش سال‌های موجود در آن محدوده)
    if fiscal_year_filter:
        try:
            fiscal_year_int = int(fiscal_year_filter)
            g_year_start, g_month_start, g_day_start = persian.to_gregorian(fiscal_year_int, 1, 1)
            try:
                g_year_end, g_month_end, g_day_end = persian.to_gregorian(fiscal_year_int, 12, 30)
            except (ValueError, OverflowError):
                g_year_end, g_month_end, g_day_end = persian.to_gregorian(fiscal_year_int, 12, 29)
            
            start_date = date(g_year_start, g_month_start, g_day_start)
            end_date = date(g_year_end, g_month_end, g_day_end)
            
            fiscal_year_query = fiscal_year_query.filter(
                InvoiceSummary.invoice_created_at >= start_date,
                InvoiceSummary.invoice_created_at <= end_date
            )
        except (ValueError, TypeError, OverflowError):
            pass
    
    # استخراج سال‌های مالی منحصر به فرد (بر اساس سال شمسی)
    # بهینه‌سازی: فقط invoice_created_at را می‌خوانیم به جای همه fields
    fiscal_years_query = fiscal_year_query.filter(
        InvoiceSummary.invoice_created_at.isnot(None)
    ).with_entities(InvoiceSummary.invoice_created_at).distinct().all()
    
    fiscal_years = set()
    for date_val in fiscal_years_query:
        if date_val[0]:  # date_val is a tuple (invoice_created_at,)
            fiscal_year = get_persian_fiscal_year(date_val[0])
            if fiscal_year:
                fiscal_years.add(fiscal_year)
    
    # برای استخراج وضعیت‌ها: اعمال فیلتر سال مالی (اگر موجود باشد)
    # اما بدون فیلتر وضعیت (تا همه وضعیت‌ها خوانده شوند)
    # مهم: status_filter هرگز برای status_query اعمال نمی‌شود
    status_query = base_query
    
    # Debug: بررسی وضعیت‌های موجود در base_query قبل از اعمال فیلتر سال مالی
    # فقط در development mode اجرا می‌شود
    import os
    if os.getenv('FLASK_DEBUG') == '1' or os.getenv('FLASK_ENV') == 'development':
        base_summaries_sample = base_query.limit(100).all()
        base_statuses = {}
        for s in base_summaries_sample:
            status = s.invoice_status or "None"
            base_statuses[status] = base_statuses.get(status, 0) + 1
        print(f"[FILTERS/OPTIONS DEBUG] Base query statuses (sample of {len(base_summaries_sample)}): {base_statuses}")
    
    print(f"[FILTERS/OPTIONS] Starting status extraction - fiscal_year={fiscal_year_filter}, status_filter={status_filter}")
    
    # اگر fiscal_year_filter موجود است، فیلتر سال مالی را اعمال می‌کنیم
    # مهم: summaries با invoice_created_at=None را هم در نظر می‌گیریم (با استفاده از or_)
    if fiscal_year_filter:
        try:
            fiscal_year_int = int(fiscal_year_filter)
            print(f"[FILTERS/OPTIONS] Filtering statuses by fiscal year: {fiscal_year_int}")
            g_year_start, g_month_start, g_day_start = persian.to_gregorian(fiscal_year_int, 1, 1)
            try:
                g_year_end, g_month_end, g_day_end = persian.to_gregorian(fiscal_year_int, 12, 30)
            except (ValueError, OverflowError):
                g_year_end, g_month_end, g_day_end = persian.to_gregorian(fiscal_year_int, 12, 29)
            
            start_date = date(g_year_start, g_month_start, g_day_start)
            end_date = date(g_year_end, g_month_end, g_day_end)
            
            print(f"[FILTERS/OPTIONS] Fiscal year date range: {start_date} to {end_date}")
            
            # اعمال فیلتر سال مالی بر اساس invoice_created_at
            # اگر invoice_created_at=None باشد، از created_at استفاده می‌کنیم
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            status_query = status_query.filter(
                or_(
                    (InvoiceSummary.invoice_created_at >= start_date) & (InvoiceSummary.invoice_created_at <= end_date),
                    (InvoiceSummary.invoice_created_at.is_(None)) & 
                    (InvoiceSummary.created_at >= start_datetime) & 
                    (InvoiceSummary.created_at <= end_datetime)
                )
            )
            
            # Debug: تعداد summaries بعد از فیلتر سال مالی
            count_after_fiscal = status_query.count()
            print(f"[FILTERS/OPTIONS] Summaries after fiscal year filter (including None dates): {count_after_fiscal}")
        except (ValueError, TypeError, OverflowError) as e:
            print(f"[FILTERS/OPTIONS] Error in fiscal year filter: {e}")
            pass
    
    # اگر status_filter موجود است، فیلتر وضعیت را اعمال می‌کنیم
    # (برای نمایش وضعیت‌های موجود در محدوده فیلترهای اعمال شده)
    if status_filter:
        status_query = status_query.filter(InvoiceSummary.invoice_status == status_filter)
        print(f"[FILTERS/OPTIONS] Filtering statuses by status: {status_filter}")
    
    # استخراج وضعیت‌های منحصر به فرد
    all_summaries = status_query.all()
    print(f"[FILTERS/OPTIONS] Extracting statuses from {len(all_summaries)} summaries")
    
    # Debug logging
    print(f"[FILTERS/OPTIONS DEBUG] Total summaries found: {len(all_summaries)}")
    if not is_expert and user.contractor:
        print(f"[FILTERS/OPTIONS DEBUG] Contractor: detail_code={user.contractor.detail_code}, supplier_code={user.contractor.supplier_code}")
    
    statuses = set()
    status_counts = {}  # تعداد هر وضعیت
    status_amounts = {}  # مبلغ کل هر وضعیت
    
    # Debug: بررسی وضعیت‌های موجود در summaries قبل از پردازش
    statuses_debug = {}
    for summary in all_summaries:
        status = summary.invoice_status or "None"
        if status not in statuses_debug:
            statuses_debug[status] = []
        fiscal_year = get_persian_fiscal_year(summary.invoice_created_at) if summary.invoice_created_at else None
        statuses_debug[status].append({
            "cover_number": summary.cover_number,
            "invoice_created_at": summary.invoice_created_at.isoformat() if summary.invoice_created_at else None,
            "fiscal_year": fiscal_year
        })
    
    print(f"[FILTERS/OPTIONS DEBUG] Status breakdown (before processing):")
    for status, items in statuses_debug.items():
        print(f"  - {status}: {len(items)} invoices")
        if len(items) <= 5:
            for item in items[:3]:
                print(f"      Cover: {item['cover_number']}, Created At: {item['invoice_created_at']}, Fiscal Year: {item['fiscal_year']}")
    
    for summary in all_summaries:
        if summary.invoice_status:
            statuses.add(summary.invoice_status)
            status_counts[summary.invoice_status] = status_counts.get(summary.invoice_status, 0) + 1
            # محاسبه مبلغ
            gross_amount = summary.gross_amount or Decimal("0")
            status_amounts[summary.invoice_status] = status_amounts.get(summary.invoice_status, Decimal("0")) + gross_amount
        else:
            print(f"[FILTERS/OPTIONS DEBUG] Summary {summary.cover_number} has no invoice_status")
    
    # Debug: نمایش وضعیت‌های پیدا شده
    print(f"[FILTERS/OPTIONS DEBUG] Statuses found: {statuses}")
    print(f"[FILTERS/OPTIONS DEBUG] Status counts: {status_counts}")
    
    # محاسبه درصد و مبلغ هر وضعیت
    total_count = len(all_summaries)
    status_stats = {}
    for status in statuses:
        count = status_counts.get(status, 0)
        percentage = round((count / total_count * 100), 1) if total_count > 0 else 0
        amount = float(status_amounts.get(status, Decimal("0")))
        status_stats[status] = {
            "count": count,
            "percentage": percentage,
            "amount": amount  # اضافه کردن مبلغ
        }
    
    print(f"[FILTERS/OPTIONS DEBUG] Status stats: {status_stats}")
    
    return jsonify({
        "fiscal_years": sorted(list(fiscal_years), reverse=True),  # از جدید به قدیم
        "statuses": sorted(list(statuses)),
        "status_stats": status_stats,  # آمار وضعیت‌ها (تعداد و درصد)
    }), 200

