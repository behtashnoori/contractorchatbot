from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd
from werkzeug.datastructures import FileStorage

from ..extensions import db
from ..models import ImportBatch, ImportError, InvoiceSummary, InvoiceDetail, utc_now
from .import_activation import (
    deactivate_active_rows,
    mark_batch_published,
    mark_previous_active_replaced,
)
from .import_utils import normalize_code, normalize_str, parse_jalali, parse_decimal

logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    inserted: int
    updated: int
    errors: int


HEADER_RULES: list[tuple[str, tuple[str, ...]]] = [
    # Core identifiers
    ("cover_number", ("شماره", "روکش")),
    ("automation_number", ("شماره", "اتوماسیون")),
    
    # Dates - ترتیب مهم است! rule های خاص‌تر باید اول باشند
    # "تاریخ ایجاد سند حسابداری فاکتور" باید قبل از "تاریخ ایجاد فاکتور" باشد
    ("invoice_date", ("تاريخ", "ایجاد", "سند", "حسابداری", "فاکتور")),  # خاص‌تر: شامل "سند" و "حسابداری"
    ("invoice_created_at", ("تاريخ", "ایجاد", "فاکتور")),  # عمومی‌تر: فقط "تاریخ ایجاد فاکتور"
    ("delivered_to_supervisor_at", ("تاریخ", "تحویل", "ناظر")),
    ("delivered_to_accounting_at", ("تاریخ", "تحویل", "حسابداری")),
    ("delivered_to_supervisor_at_alt", ("در", "اختیار", "ناظر")),  # این یک عدد است، نه تاریخ
    
    # Basic info
    ("business_owner", ("بهره", "بردار")),
    ("cost_subject", ("موضوع", "هزینه", "فاکتور", "خرید")),
    ("gross_amount", ("مبلغ", "کل")),
    ("net_amount", ("مبلغ", "بدون", "مال")),
    ("time_span", ("محدوده", "زمانی", "انجام", "کار")),
    ("invoice_status", ("وضعیت", "فاکتور")),
    ("notes", ("توضیحات", "فاکتور", "خرید")),
    
    # Invoice numbers
    ("contractor_invoice_no", ("شماره", "صورت", "حساب", "پیمانکار", "فاکتور", "خرید")),
    ("permit_number", ("شماره", "مجوز", "فاکتور", "خرید")),
    ("permit_type", ("نوع", "مجوز", "فاکتور", "خرید")),
    
    # Client info
    ("client_name", ("نام", "کارفرما")),
    ("client_contract_number", ("شماره", "قرارداد", "کارفرما", "فاکتور", "خرید")),
    
    # Supplier info (for contractor lookup)
    ("supplier_name", ("نام", "تامین", "کننده")),
    ("detail_code", ("کد", "تفصیلی")),
    ("supplier_code", ("کد", "تامین", "کننده")),
]

REQUIRED_KEYS = ("cover_number", "invoice_status")


class ContractorsOneImporter:
    """Importer for contractors-1 Excel source (invoice summary style data)."""

    def __init__(self, batch: ImportBatch):
        self.batch = batch

    def run(self, file_obj: FileStorage) -> ImportResult:
        try:
            logger.info("Reading Excel file")
            dataframe = pd.read_excel(file_obj)
            logger.info("Excel file read successfully, rows=%s", len(dataframe))
        except Exception as exc:  # pragma: no cover
            raise ValueError("خطا در خواندن فایل اکسل") from exc

        logger.info("Mapping headers")
        column_map = self._map_headers(dataframe.columns)
        logger.info("Mapped %s columns", len(column_map))
        missing = [key for key in REQUIRED_KEYS if key not in column_map]
        if missing:
            raise ValueError(f"ستون های حیاتی یافت نشدند: {', '.join(missing)}")

        preflight_insert_data, preflight_error_records = self._preflight_rows(dataframe, column_map)
        if not preflight_insert_data:
            raise ValueError("contractors-1 import has no valid invoice summary rows.")
        logger.info(
            "Preflight completed for contractors-1: valid_rows=%s row_errors=%s",
            len(preflight_insert_data),
            len(preflight_error_records),
        )
        return self._publish_preflight_rows(
            preflight_insert_data,
            preflight_error_records,
            len(dataframe),
        )


    def _preflight_rows(self, dataframe: pd.DataFrame, column_map: dict[str, str]) -> tuple[list[dict], list[dict]]:
        insert_data: list[dict] = []
        error_records: list[dict] = []

        for idx, row_dict in enumerate(dataframe.to_dict('records')):
            try:
                cover_number = normalize_str(self._value_for_dict(row_dict, column_map, "cover_number"))
                if not cover_number:
                    raise ValueError("شماره روکش خالی است")

                if len(cover_number) > 64:
                    cover_number = cover_number[:64]

                data = self._prepare_summary_data(row_dict, column_map, cover_number)
                now = utc_now()
                data['created_at'] = now
                data['updated_at'] = now
                insert_data.append(data)
            except Exception as exc:
                now = utc_now()
                error_records.append({
                    'batch_id': self.batch.id,
                    'source_file': 'contractors-1',
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
            logger.info("Publishing preflighted contractors-1 rows in one transaction")
            mark_previous_active_replaced("contractors-1", self.batch)
            deactivate_active_rows("contractors-1")

            self.batch.total_rows = total_rows
            self.batch.rows_processed = total_rows
            self.batch.progress_percentage = 100.0 if total_rows else 0.0
            mark_batch_published(self.batch)

            if insert_data:
                for row in insert_data:
                    row["is_active"] = True
                db.session.bulk_insert_mappings(InvoiceSummary, insert_data)
            if error_records:
                db.session.bulk_insert_mappings(ImportError, error_records)

            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception("contractors-1 publish failed; transaction rolled back")
            raise

        logger.info(
            "Final commit completed: inserted=%s updated=%s errors=%s",
            inserted,
            updated,
            errors,
        )
        return ImportResult(inserted=inserted, updated=updated, errors=errors)

    def _map_headers(self, columns: list[Any]) -> dict[str, str]:
        mapping: dict[str, str] = {}
        # Normalize columns using normalize_str from import_utils (same as codtafsiltamin)
        normalized_columns = {normalize_str(str(col)) or str(col).strip(): col for col in columns}
        used_columns = set()  # Track which columns have been matched
        
        # Sort rules by specificity (more tokens = more specific)
        sorted_rules = sorted(HEADER_RULES, key=lambda x: len(x[1]), reverse=True)
        
        for key, tokens in sorted_rules:
            for normalized, original in normalized_columns.items():
                if normalized and original not in used_columns:
                    if all(token in normalized for token in tokens):
                        mapping[key] = original
                        used_columns.add(original)
                        break  # Move to next rule after finding a match
        return mapping

    def _prepare_summary_data(self, row_dict: dict, column_map: dict[str, str], cover_number: str) -> dict:
        """Prepare data dictionary for bulk insert/update"""
        def get_value(key: str):
            col = column_map.get(key)
            return row_dict.get(col) if col else None
        
        # Prepare all fields with truncation
        automation_number = normalize_str(get_value("automation_number"))
        invoice_status = normalize_str(get_value("invoice_status"))
        permit_number = normalize_str(get_value("permit_number"))
        permit_type = normalize_str(get_value("permit_type"))
        client_contract_number = normalize_str(get_value("client_contract_number"))
        contractor_invoice_no = normalize_str(get_value("contractor_invoice_no"))
        time_span = normalize_str(get_value("time_span"))
        
        # Handle supervisor dates
        # delivered_to_supervisor_at از "تاریخ تحویل ناظر" می‌آید (نه از "در اختیار ناظر" که عدد است)
        delivered_to_supervisor_at = parse_jalali(get_value("delivered_to_supervisor_at"))
        
        data = {
            'cover_number': cover_number,
            'detail_code': normalize_code(get_value("detail_code")),
            'supplier_code': normalize_code(get_value("supplier_code")),
            'automation_number': automation_number[:64] if automation_number else None,
            'invoice_status': invoice_status[:64] if invoice_status else None,
            'permit_number': permit_number[:128] if permit_number else None,
            'permit_type': permit_type[:128] if permit_type else None,
            'client_contract_number': client_contract_number[:128] if client_contract_number else None,
            'contractor_invoice_no': contractor_invoice_no[:128] if contractor_invoice_no else None,
            'time_span': time_span[:128] if time_span else None,
            'client_name': normalize_str(get_value("client_name")),
            'business_owner': normalize_str(get_value("business_owner")),
            'cost_subject': normalize_str(get_value("cost_subject")),
            'notes': normalize_str(get_value("notes")),
            'invoice_date': parse_jalali(get_value("invoice_date")),
            'invoice_created_at': parse_jalali(get_value("invoice_created_at")),
            'delivered_to_supervisor_at': delivered_to_supervisor_at,
            'delivered_to_accounting_at': parse_jalali(get_value("delivered_to_accounting_at")),
            'gross_amount': parse_decimal(get_value("gross_amount")),
            'net_amount': parse_decimal(get_value("net_amount")),
            'raw_payload': self._prepare_raw_payload(row_dict, column_map),  # Optimized payload
            'last_update_batch_id': self.batch.id,
        }
        return data

    def _prepare_raw_payload(self, row_dict: dict, column_map: dict[str, str]) -> dict:
        """Prepare optimized raw_payload - only include mapped columns to reduce size"""
        # Only include columns that are actually mapped (relevant data)
        # This significantly reduces payload size and improves performance
        payload = {}
        for key, col_name in column_map.items():
            if col_name in row_dict:
                value = row_dict[col_name]
                # Skip NaN/None values
                try:
                    if pd.isna(value):
                        continue
                except (TypeError, ValueError):
                    # If pd.isna fails, check for None
                    if value is None:
                        continue
                
                # Convert pandas types to native Python types for JSON serialization
                if isinstance(value, pd.Timestamp):
                    value = str(value)
                elif isinstance(value, (int, float)):
                    # Keep numeric values as-is
                    pass
                payload[str(col_name)] = value
        return payload

    def _value_for_dict(self, row_dict: dict, column_map: dict[str, str], key: str) -> Any:
        """Get value from dict row (faster than Series)"""
        column = column_map.get(key)
        if column is None:
            return None
        return row_dict.get(column)


