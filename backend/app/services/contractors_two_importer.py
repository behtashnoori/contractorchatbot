from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
from convertdate import persian
from werkzeug.datastructures import FileStorage

from ..extensions import db
from ..models import ImportBatch, ImportError, InvoiceDetail, InvoiceSummary, utc_now
from .import_activation import (
    active_filter,
    deactivate_active_rows,
    mark_batch_published,
    mark_previous_active_replaced,
)

logger = logging.getLogger(__name__)

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

COLUMN_ALIASES: dict[str, list[str]] = {
    "cover_number": ["شماره", "شماره روکش"],  # ستون "شماره" در فایل 2 همان cover_number است
    "invoice_date": ["تاریخ", "تاريخ"],
    "unit_code": ["احد", "رمز", "تامبر", "واحد"],
    "supplier_name": ["تامین کننده", "تامين كننده"],
    "status": ["وضعیت", "وضعيت"],
    "item_title": ["عنوان قلم خرید", "قلم خرید", "قلم خریدار"],
    "gross_amount": ["مبلغ ناخالص", "مبلغ نا خالص"],
    "reference": ["مبنا", "مبناء"],
    "description": ["توضیحات", "توضيحات"],
}

REQUIRED_FIELDS = ["cover_number", "invoice_date", "supplier_name", "gross_amount"]  # cover_number از ستون "شماره" خوانده می‌شود


@dataclass
class ImportResult:
    inserted: int
    updated: int
    errors: int


class ContractorsTwoImporter:
    """Importer for contractors-2 Excel source (invoice detail style data)."""

    def __init__(self, batch: ImportBatch):
        self.batch = batch
        self.column_map: dict[str, str] = {}

    def run(self, file_obj: FileStorage) -> ImportResult:
        try:
            logger.info("Reading Excel file")
            dataframe = pd.read_excel(file_obj)
            logger.info("Excel file read successfully, rows=%s", len(dataframe))
        except Exception as exc:
            raise ValueError("خطا در خواندن فایل اکسل") from exc

        self._prepare_columns(dataframe)
        preflight_insert_data, preflight_error_records = self._preflight_rows(dataframe)
        if not preflight_insert_data:
            raise ValueError("contractors-2 import has no valid invoice detail rows.")
        logger.info(
            "Preflight completed for contractors-2: valid_rows=%s row_errors=%s",
            len(preflight_insert_data),
            len(preflight_error_records),
        )
        return self._publish_preflight_rows(
            preflight_insert_data,
            preflight_error_records,
            len(dataframe),
        )


    def _preflight_rows(self, dataframe: pd.DataFrame) -> tuple[list[dict], list[dict]]:
        rows_dict = dataframe.to_dict('records')
        cover_numbers_in_file = set()
        for row_dict in rows_dict:
            cover_number = self._normalize_code(self._value_for_dict(row_dict, "cover_number"))
            if cover_number:
                cover_numbers_in_file.add(cover_number)

        summaries_by_cover = {
            s.cover_number: s
            for s in InvoiceSummary.query.filter(
                active_filter(InvoiceSummary),
                InvoiceSummary.cover_number.in_(cover_numbers_in_file)
            ).all()
        }

        insert_data: list[dict] = []
        error_records: list[dict] = []
        for idx, row_dict in enumerate(rows_dict):
            try:
                cover_number = self._normalize_code(self._value_for_dict(row_dict, "cover_number"))
                if not cover_number:
                    raise ValueError("شماره روکش خالی است")

                summary = summaries_by_cover.get(cover_number)
                data = self._prepare_detail_data(row_dict, cover_number, summary, idx)
                now = utc_now()
                data['created_at'] = now
                data['updated_at'] = now
                insert_data.append(data)
            except Exception as exc:
                now = utc_now()
                error_records.append({
                    'batch_id': self.batch.id,
                    'source_file': 'contractors-2',
                    'row_index': idx + 2,
                    'message': str(exc)[:255],
                    'payload': row_dict,
                    'created_at': now,
                    'updated_at': now,
                })

        return insert_data, error_records

    def _publish_preflight_rows(
        self,
        insert_data: list[dict],
        error_records: list[dict],
        total_rows: int,
    ) -> ImportResult:
        inserted = len(insert_data)
        updated = 0
        errors = len(error_records)

        try:
            logger.info("Publishing preflighted contractors-2 rows in one transaction")
            mark_previous_active_replaced("contractors-2", self.batch)
            deactivate_active_rows("contractors-2")

            self.batch.total_rows = total_rows
            self.batch.rows_processed = total_rows
            self.batch.progress_percentage = 100.0 if total_rows else 0.0
            mark_batch_published(self.batch)

            if insert_data:
                for row in insert_data:
                    row["is_active"] = True
                db.session.bulk_insert_mappings(InvoiceDetail, insert_data)
            if error_records:
                db.session.bulk_insert_mappings(ImportError, error_records)

            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception("contractors-2 publish failed; transaction rolled back")
            raise

        logger.info("Final commit completed: inserted=%s errors=%s", inserted, errors)
        return ImportResult(inserted=inserted, updated=updated, errors=errors)

    def _prepare_columns(self, frame: pd.DataFrame) -> None:
        columns = [str(col).strip() for col in frame.columns]
        resolved: dict[str, str] = {}
        for field, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                for column in columns:
                    if alias.replace(" ", "") in column.replace(" ", ""):
                        resolved[field] = column
                        break
                if field in resolved:
                    break

        missing = [field for field in REQUIRED_FIELDS if field not in resolved]
        if missing:
            raise ValueError("ستون‌های الزامی یافت نشدند")
        self.column_map = resolved

    def _prepare_detail_data(self, row_dict: dict, cover_number: str, summary: InvoiceSummary | None = None, row_index: int = 0) -> dict:
        """Prepare data dictionary for bulk insert/update"""
        def get_value(key: str):
            col = self.column_map.get(key)
            return row_dict.get(col) if col else None
        
        # استخراج detail_code و supplier_code از InvoiceSummary
        detail_code = None
        supplier_code = None
        if summary:
            detail_code = summary.detail_code
            supplier_code = summary.supplier_code
        else:
            # اگر summary موجود نبود، از query استفاده می‌کنیم (فقط برای موارد نادر)
            summary = InvoiceSummary.query.filter(
                active_filter(InvoiceSummary),
                InvoiceSummary.cover_number == cover_number,
            ).first()
            if summary:
                detail_code = summary.detail_code
                supplier_code = summary.supplier_code
        
        # استخراج reference برای ساخت invoice_no یکتا
        reference = self._normalize_text(get_value("reference"))
        
        # ساخت invoice_no یکتا: cover_number-reference یا cover_number-index
        if reference:
            invoice_no = f"{cover_number}-{reference}"
        else:
            invoice_no = f"{cover_number}-{row_index}"
        
        data = {
            'invoice_no': invoice_no,  # ترکیبی: cover_number-reference یا cover_number-index
            'cover_number': cover_number,  # از ستون "شماره" در فایل 2
            'detail_code': detail_code,  # از InvoiceSummary
            'supplier_code': supplier_code,  # از InvoiceSummary
            'invoice_date': self._parse_jalali(get_value("invoice_date")),
            'unit_code': self._normalize_text(get_value("unit_code")),
            'supplier_name': self._normalize_text(get_value("supplier_name")),
            'status': self._normalize_text(get_value("status")),
            'item_title': self._normalize_text(get_value("item_title")),
            'gross_amount': self._parse_decimal(get_value("gross_amount")),
            'reference': reference,
            'description': self._normalize_text(get_value("description")),
            'raw_payload': self._prepare_raw_payload(row_dict),
            'last_update_batch_id': self.batch.id,
        }
        return data

    def _prepare_raw_payload(self, row_dict: dict) -> dict:
        """Prepare optimized raw_payload - only include mapped columns to reduce size"""
        payload = {}
        for key, col_name in self.column_map.items():
            if col_name in row_dict:
                value = row_dict[col_name]
                # Skip NaN/None values
                try:
                    if pd.isna(value):
                        continue
                except (TypeError, ValueError):
                    if value is None:
                        continue
                
                # Convert pandas types to native Python types for JSON serialization
                if isinstance(value, pd.Timestamp):
                    value = str(value)
                elif isinstance(value, (int, float)):
                    pass
                payload[str(col_name)] = value
        return payload

    def _value_for_dict(self, row_dict: dict, key: str) -> Any:
        """Get value from dict row (faster than Series)"""
        column = self.column_map.get(key)
        if column is None:
            return None
        return row_dict.get(column)

    def _value(self, row: pd.Series, field: str) -> Any:
        column = self.column_map.get(field)
        if column is None:
            return None
        return row.get(column)

    def _row_payload(self, row: pd.Series) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for column in row.index:
            payload[str(column)] = self._safe_value(row[column])
        return payload

    def _safe_value(self, value: Any) -> Any:
        if pd.isna(value):
            return None
        if isinstance(value, date):
            return value.isoformat()
        return str(value).strip()

    def _normalize_text(self, value: Any) -> str | None:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        text = str(value).strip().translate(PERSIAN_DIGITS)
        return text or None

    def _normalize_code(self, value: Any) -> str | None:
        text = self._normalize_text(value)
        if not text:
            return None
        return text.replace(" ", "")

    def _parse_decimal(self, value: Any) -> Decimal | None:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value))
        text = str(value).strip().translate(PERSIAN_DIGITS)
        if not text:
            return None
        text = text.replace(",", "")
        try:
            return Decimal(text)
        except InvalidOperation:
            return None

    def _parse_jalali(self, value: Any) -> date | None:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        if isinstance(value, date):
            return value
        text = str(value).strip().translate(PERSIAN_DIGITS)
        if not text:
            return None
        text = text.replace("-", "/")
        parts = text.split("/")
        if len(parts) != 3:
            return None
        try:
            year, month, day = (int(part) for part in parts)
        except ValueError:
            return None
        g_year, g_month, g_day = persian.to_gregorian(year, month, day)
        return date(g_year, g_month, g_day)
