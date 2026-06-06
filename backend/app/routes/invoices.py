from __future__ import annotations

from decimal import Decimal
from datetime import datetime, date

from flask import Blueprint, g, jsonify, request
from sqlalchemy import distinct, or_, select
from convertdate import persian

from ..extensions import db
from ..models import InvoiceDetail, InvoiceSummary, User
from ..services.audit_log import (
    ACTION_INVOICE_VIEW,
    ENTITY_INVOICE_SUMMARY,
    record_audit,
)
from ..services.import_activation import active_filter, active_query
from ..utils.api_errors import error_response
from ..utils.auth_decorators import require_jwt_user
from ..utils.auth_utils import user_has_staff_access

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


def _invoice_summary_base_query_for_user(user: User):
    """
    Staff: all invoice summaries. Contractor: scoped summaries (detail_code + optional cover fallback).
    Returns None if the user is a contractor without a linked contractor row.
    """
    if user_has_staff_access(user):
        return active_query(InvoiceSummary)
    if not user.contractor:
        return None
    contractor = user.contractor
    conditions = []
    detail_code_condition = InvoiceSummary.detail_code == contractor.detail_code
    conditions.append(detail_code_condition)
    if contractor.supplier_code:
        matching_cover_numbers_subquery = select(distinct(InvoiceDetail.cover_number)).where(
            active_filter(InvoiceDetail),
            (InvoiceDetail.supplier_code == contractor.supplier_code)
            | (InvoiceDetail.supplier_code.is_(None))
        ).scalar_subquery()
        fallback_condition = (
            InvoiceSummary.cover_number.in_(matching_cover_numbers_subquery)
            & (InvoiceSummary.detail_code != contractor.detail_code)
        )
        conditions.append(fallback_condition)
    if len(conditions) > 1:
        query = active_query(InvoiceSummary).filter(or_(*conditions))
    else:
        query = active_query(InvoiceSummary).filter(conditions[0])
    if contractor.supplier_code:
        query = query.filter(
            (InvoiceSummary.supplier_code == contractor.supplier_code)
            | (InvoiceSummary.supplier_code.is_(None))
        )
    return query


def _persian_fiscal_year_date_bounds(fiscal_year_int: int) -> tuple[date, date] | None:
    """Gregorian (start, end) date range for Persian fiscal year ``fiscal_year_int``, or None if invalid."""
    try:
        g_year_start, g_month_start, g_day_start = persian.to_gregorian(fiscal_year_int, 1, 1)
        try:
            g_year_end, g_month_end, g_day_end = persian.to_gregorian(fiscal_year_int, 12, 30)
        except (ValueError, OverflowError):
            g_year_end, g_month_end, g_day_end = persian.to_gregorian(fiscal_year_int, 12, 29)
        return (
            date(g_year_start, g_month_start, g_day_start),
            date(g_year_end, g_month_end, g_day_end),
        )
    except (ValueError, TypeError, OverflowError):
        return None


def _fallback_summary_for_contractor_cover(
    cover_number: str, contractor
) -> InvoiceSummary | None:
    """When primary detail_code-scoped summary is missing, resolve via detail rows + supplier scope."""
    any_summary = active_query(InvoiceSummary).filter_by(cover_number=cover_number).first()
    if not any_summary:
        return None
    test_details = active_query(InvoiceDetail).filter_by(cover_number=cover_number)
    if contractor.supplier_code:
        test_details = test_details.filter(
            (InvoiceDetail.supplier_code == contractor.supplier_code)
            | (InvoiceDetail.supplier_code.is_(None))
        )
    if not test_details.first():
        return None
    fallback_summary_query = active_query(InvoiceSummary).filter_by(cover_number=cover_number)
    if contractor.supplier_code:
        fallback_summary_query = fallback_summary_query.filter(
            (InvoiceSummary.supplier_code == contractor.supplier_code)
            | (InvoiceSummary.supplier_code.is_(None))
        )
    summary = fallback_summary_query.order_by(InvoiceSummary.updated_at.desc()).first()
    if summary is None:
        return active_query(InvoiceSummary).filter_by(cover_number=cover_number).order_by(
            InvoiceSummary.updated_at.desc()
        ).first()
    return summary


def _contractor_invoice_detail_scope(cover_number: str, contractor):
    """Details query and summary for contractor-scoped invoice detail view."""
    summary_query = active_query(InvoiceSummary).filter_by(
        cover_number=cover_number, detail_code=contractor.detail_code
    )
    if contractor.supplier_code:
        summary_query = summary_query.filter(
            (InvoiceSummary.supplier_code == contractor.supplier_code)
            | (InvoiceSummary.supplier_code.is_(None))
        )
    details_query = active_query(InvoiceDetail).filter_by(cover_number=cover_number)
    if contractor.supplier_code:
        details_query = details_query.filter(
            (InvoiceDetail.supplier_code == contractor.supplier_code)
            | (InvoiceDetail.supplier_code.is_(None))
        )
    summary = summary_query.order_by(InvoiceSummary.updated_at.desc()).first()
    if summary is None:
        summary = _fallback_summary_for_contractor_cover(cover_number, contractor)
    return details_query, summary


@invoices_bp.get("/")
@require_jwt_user
def list_invoices():
    user = g.current_user

    query = _invoice_summary_base_query_for_user(user)
    if query is None:
        return error_response(
            404,
            "not_found",
            "No contractor linked to this account.",
        )

    staff_access = user_has_staff_access(user)

    # فیلتر وضعیت: پشتیبانی از هم string و هم array
    status = request.args.getlist("status")
    if not status:
        # اگر getlist چیزی برنگرداند، get را امتحان کنیم (برای string)
        status_str = request.args.get("status")
        if status_str:
            status = [status_str]
    
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
    
    # فیلتر بر اساس سال مالی شمسی
    # سال مالی شمسی: از 1 فروردین شروع می‌شود
    fiscal_year = request.args.get("fiscal_year")
    if fiscal_year:
        try:
            fiscal_year_int = int(fiscal_year)
            g_year_start, g_month_start, g_day_start = persian.to_gregorian(fiscal_year_int, 1, 1)
            try:
                g_year_end, g_month_end, g_day_end = persian.to_gregorian(fiscal_year_int, 12, 29)
                try:
                    g_year_end_30, g_month_end_30, g_day_end_30 = persian.to_gregorian(
                        fiscal_year_int, 12, 30
                    )
                    g_year_end, g_month_end, g_day_end = (
                        g_year_end_30,
                        g_month_end_30,
                        g_day_end_30,
                    )
                except (ValueError, OverflowError):
                    pass
            except (ValueError, OverflowError):
                g_year_end, g_month_end, g_day_end = persian.to_gregorian(fiscal_year_int, 12, 28)

            start_date = date(g_year_start, g_month_start, g_day_start)
            end_date = date(g_year_end, g_month_end, g_day_end)

            query = query.filter(
                InvoiceSummary.invoice_created_at >= start_date,
                InvoiceSummary.invoice_created_at <= end_date,
            )

        except (ValueError, TypeError, OverflowError):
            pass

    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(max(int(request.args.get("page_size", 20)), 1), 100)

    pagination = query.order_by(InvoiceSummary.invoice_created_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )

    items = []
    pending_amount = Decimal("0")
    approved_amount = Decimal("0")
    total_invoices = pagination.total

    # بهینه‌سازی: یک query برای همه details به جای N+1 queries
    cover_numbers = [s.cover_number for s in pagination.items]
    detail_codes = list(set([s.detail_code for s in pagination.items if s.detail_code]))
    
    # یک query برای همه details مربوط به summaries در این صفحه
    all_details_query = active_query(InvoiceDetail).filter(
        InvoiceDetail.cover_number.in_(cover_numbers)
    )
    if detail_codes:
        all_details_query = all_details_query.filter(InvoiceDetail.detail_code.in_(detail_codes))
    
    if not staff_access and user.contractor and user.contractor.supplier_code:
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
@require_jwt_user
def invoice_detail(cover_number: str):
    user = g.current_user
    staff_access = user_has_staff_access(user)

    if staff_access:
        # کارشناس: همه فاکتورها را می‌بیند
        summary_query = active_query(InvoiceSummary).filter_by(cover_number=cover_number)
        details_query = active_query(InvoiceDetail).filter_by(cover_number=cover_number)
        summary = summary_query.order_by(InvoiceSummary.updated_at.desc()).first()
    else:
        # پیمانکار: فقط فاکتورهای خودش را می‌بیند
        if not user.contractor:
            return error_response(
                404,
                "not_found",
                "No contractor linked to this account.",
            )

        contractor = user.contractor
        details_query, summary = _contractor_invoice_detail_scope(cover_number, contractor)

    if not summary:
        return error_response(404, "not_found", "Invoice not found.")

    record_audit(user.id, ACTION_INVOICE_VIEW, ENTITY_INVOICE_SUMMARY, summary.id.hex)

    detail_rows = []
    all_supplier_invoice_numbers = []

    details = details_query.order_by(InvoiceDetail.invoice_date.desc()).all()
    
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


@invoices_bp.get("/filters/options")
@require_jwt_user
def get_filter_options():
    """
    دریافت لیست سال‌های مالی و وضعیت‌های موجود برای فیلتر
    """
    user = g.current_user

    base_query = _invoice_summary_base_query_for_user(user)
    if base_query is None:
        return error_response(
            404,
            "not_found",
            "No contractor linked to this account.",
        )

    fiscal_year_filter = request.args.get("fiscal_year")
    status_filter = request.args.get("status")

    fiscal_year_query = base_query
    if status_filter:
        fiscal_year_query = fiscal_year_query.filter(InvoiceSummary.invoice_status == status_filter)

    # اگر فیلتر سال مالی موجود باشد، آن را اعمال می‌کنیم (برای نمایش سال‌های موجود در آن محدوده)
    if fiscal_year_filter:
        try:
            fiscal_year_int = int(fiscal_year_filter)
            bounds = _persian_fiscal_year_date_bounds(fiscal_year_int)
            if bounds:
                start_date, end_date = bounds
                fiscal_year_query = fiscal_year_query.filter(
                    InvoiceSummary.invoice_created_at >= start_date,
                    InvoiceSummary.invoice_created_at <= end_date,
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
    
    status_query = base_query

    if fiscal_year_filter:
        try:
            fiscal_year_int = int(fiscal_year_filter)
            bounds = _persian_fiscal_year_date_bounds(fiscal_year_int)
            if bounds:
                start_date, end_date = bounds
                start_datetime = datetime.combine(start_date, datetime.min.time())
                end_datetime = datetime.combine(end_date, datetime.max.time())
                status_query = status_query.filter(
                    or_(
                        (InvoiceSummary.invoice_created_at >= start_date)
                        & (InvoiceSummary.invoice_created_at <= end_date),
                        (InvoiceSummary.invoice_created_at.is_(None))
                        & (InvoiceSummary.created_at >= start_datetime)
                        & (InvoiceSummary.created_at <= end_datetime),
                    )
                )
        except (ValueError, TypeError, OverflowError):
            pass

    if status_filter:
        status_query = status_query.filter(InvoiceSummary.invoice_status == status_filter)

    all_summaries = status_query.all()

    statuses = set()
    status_counts = {}
    status_amounts = {}

    for summary in all_summaries:
        if summary.invoice_status:
            statuses.add(summary.invoice_status)
            status_counts[summary.invoice_status] = status_counts.get(summary.invoice_status, 0) + 1
            gross_amount = summary.gross_amount or Decimal("0")
            status_amounts[summary.invoice_status] = status_amounts.get(
                summary.invoice_status, Decimal("0")
            ) + gross_amount

    total_count = len(all_summaries)
    status_stats = {}
    for status in statuses:
        count = status_counts.get(status, 0)
        percentage = round((count / total_count * 100), 1) if total_count > 0 else 0
        amount = float(status_amounts.get(status, Decimal("0")))
        status_stats[status] = {
            "count": count,
            "percentage": percentage,
            "amount": amount,
        }
    
    return jsonify({
        "fiscal_years": sorted(list(fiscal_years), reverse=True),  # از جدید به قدیم
        "statuses": sorted(list(statuses)),
        "status_stats": status_stats,  # آمار وضعیت‌ها (تعداد و درصد)
    }), 200
