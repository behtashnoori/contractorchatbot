from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
from convertdate import persian
from werkzeug.datastructures import FileStorage

from ..extensions import db
from ..models import ImportBatch, ImportError, InvoiceDetail, InvoiceSummary

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

        # Delete all existing data before importing new data
        logger.info("Deleting existing data")

        # First, delete all InvoiceDetail records (they reference ImportBatch)
        deleted_details = db.session.query(InvoiceDetail).delete()
        logger.info("Deleted %s existing InvoiceDetail records", deleted_details)
        
        # Then delete ImportError records for contractors-2 batches (excluding current batch)
        contractors_two_batch_ids = [
            batch.id for batch in ImportBatch.query.filter_by(source="contractors-2").all()
            if batch.id != self.batch.id  # Exclude current batch
        ]
        if contractors_two_batch_ids:
            deleted_errors = ImportError.query.filter(ImportError.batch_id.in_(contractors_two_batch_ids)).delete()
            logger.info("Deleted %s ImportError records", deleted_errors)
        
        # Finally delete ImportBatch records (excluding current batch)
        deleted_batches = ImportBatch.query.filter(
            ImportBatch.source == "contractors-2",
            ImportBatch.id != self.batch.id  # Exclude current batch
        ).delete()
        logger.info("Deleted %s ImportBatch records", deleted_batches)
        
        db.session.commit()

        inserted, updated, errors = 0, 0, 0
        total_rows = len(dataframe)
        
        # Update batch with total rows
        self.batch.total_rows = total_rows
        self.batch.rows_processed = 0
        self.batch.progress_percentage = 0.0
        db.session.commit()
        
        # Use COPY command for large files (>1000 rows) - much faster
        USE_COPY = total_rows > 1000
        if USE_COPY:
            logger.info("Using COPY command for large file (%s rows)", total_rows)
            return self._run_with_copy(dataframe, total_rows)
        
        # Adaptive batch size: larger batches for larger files, but cap at 1000
        BATCH_SIZE = min(max(200, total_rows // 10), 1000)
        logger.info("Using batch size: %s for %s rows", BATCH_SIZE, total_rows)
        
        rows_dict = dataframe.to_dict('records')
        
        # First pass: collect all cover_numbers for InvoiceSummary lookup
        cover_numbers_in_file = set()
        for row_dict in rows_dict:
            cover_number = self._normalize_code(self._value_for_dict(row_dict, "cover_number"))  # ستون "شماره" همان cover_number است
            if cover_number:
                cover_numbers_in_file.add(cover_number)

        # Pre-load InvoiceSummary records برای استخراج detail_code و supplier_code
        summaries_by_cover = {
            s.cover_number: s
            for s in InvoiceSummary.query.filter(
                InvoiceSummary.cover_number.in_(cover_numbers_in_file)
            ).all()
        }
        logger.info(
            "Loaded %s InvoiceSummary records for cover_number mapping",
            len(summaries_by_cover),
        )
        
        # Prepare bulk data
        logger.info("Processing %s rows", total_rows)
        
        insert_data = []
        error_records = []
        
        # Disable autoflush for better performance
        original_autoflush = db.session.autoflush
        db.session.autoflush = False
        
        try:
            for idx, row_dict in enumerate(rows_dict):
                try:
                    # در فایل 2، ستون "شماره" همان cover_number است
                    cover_number = self._normalize_code(self._value_for_dict(row_dict, "cover_number"))
                    if not cover_number:
                        raise ValueError("شماره روکش خالی است")
                    
                    # استفاده از summary برای استخراج detail_code و supplier_code
                    summary = summaries_by_cover.get(cover_number)
                    
                    # Prepare data dict - invoice_no به صورت ترکیبی ساخته می‌شود
                    data = self._prepare_detail_data(row_dict, cover_number, summary, idx)
                    
                    # Always insert new (no update logic)
                    data['created_at'] = datetime.utcnow()
                    data['updated_at'] = datetime.utcnow()
                    insert_data.append(data)
                    inserted += 1
                    
                    # Batch processing
                    if (idx + 1) % BATCH_SIZE == 0:
                        self._bulk_process_insert_only(insert_data, error_records)
                        insert_data = []
                        error_records = []
                        
                        # Update progress
                        self.batch.update_progress(idx + 1, total_rows)
                        
                        logger.info(
                            "Processed batch: %s/%s rows inserted=%s errors=%s",
                            idx + 1,
                            total_rows,
                            inserted,
                            errors,
                        )
                        
                except Exception as exc:
                    errors += 1
                    now = datetime.utcnow()
                    error_records.append({
                        'batch_id': self.batch.id,
                        'source_file': 'contractors-2',
                        'row_index': idx + 2,
                        'message': str(exc)[:255],
                        'payload': row_dict,
                        'created_at': now,
                        'updated_at': now,
                    })
            
            # Final batch
            if insert_data or error_records:
                self._bulk_process_insert_only(insert_data, error_records)
            
            # Final progress update
            self.batch.update_progress(total_rows, total_rows)
            
        finally:
            # Restore original autoflush setting
            db.session.autoflush = original_autoflush
        
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
            summary = InvoiceSummary.query.filter_by(cover_number=cover_number).first()
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

    def _bulk_process(self, insert_data: list, update_data: list, error_records: list):
        """Bulk insert/update and error handling - commits after each batch for better performance"""
        try:
            if insert_data:
                db.session.bulk_insert_mappings(InvoiceDetail, insert_data)
            if update_data:
                db.session.bulk_update_mappings(InvoiceDetail, update_data)
            if error_records:
                db.session.bulk_insert_mappings(ImportError, error_records)
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            logger.exception("Error in _bulk_process: %s", exc)
            traceback.print_exc()
            raise

    def _bulk_process_insert_only(self, insert_data: list, error_records: list):
        """Bulk insert only (no update) - commits after each batch for better performance"""
        try:
            if insert_data:
                db.session.bulk_insert_mappings(InvoiceDetail, insert_data)
            if error_records:
                db.session.bulk_insert_mappings(ImportError, error_records)
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            logger.exception("Error in _bulk_process_insert_only: %s", exc)
            traceback.print_exc()
            raise

    def _run_with_copy(self, dataframe: pd.DataFrame, total_rows: int) -> ImportResult:
        """Use PostgreSQL COPY command for fast bulk insert (10-50x faster for large files)"""
        inserted, updated, errors = 0, 0, 0
        rows_dict = dataframe.to_dict('records')
        
        # Pre-load cover_numbers (در فایل 2، ستون "شماره" همان cover_number است)
        cover_numbers_in_file = set()
        for row_dict in rows_dict:
            cover_number = self._normalize_code(self._value_for_dict(row_dict, "cover_number"))  # ستون "شماره"
            if cover_number:
                cover_numbers_in_file.add(cover_number)
        
        # Pre-load InvoiceSummary records برای استخراج detail_code و supplier_code
        summaries_by_cover = {
            s.cover_number: s
            for s in InvoiceSummary.query.filter(
                InvoiceSummary.cover_number.in_(cover_numbers_in_file)
            ).all()
        }
        
        # Prepare data (only insert, no update)
        insert_rows = []
        error_records = []
        
        for idx, row_dict in enumerate(rows_dict):
            try:
                # در فایل 2، ستون "شماره" همان cover_number است
                cover_number = self._normalize_code(self._value_for_dict(row_dict, "cover_number"))
                if not cover_number:
                    raise ValueError("شماره روکش خالی است")
                
                # استفاده از summary برای استخراج detail_code و supplier_code
                summary = summaries_by_cover.get(cover_number)
                data = self._prepare_detail_data(row_dict, cover_number, summary, idx)
                
                # Always insert new (no update logic)
                data['created_at'] = datetime.utcnow()
                data['updated_at'] = datetime.utcnow()
                insert_rows.append(data)
                inserted += 1
                
                # Update progress every 100 rows
                if (idx + 1) % 100 == 0:
                    self.batch.update_progress(idx + 1, total_rows)
                    
            except Exception as exc:
                errors += 1
                now = datetime.utcnow()
                error_records.append({
                    'batch_id': self.batch.id,
                    'source_file': 'contractors-2',
                    'row_index': idx + 2,
                    'message': str(exc)[:255],
                    'payload': row_dict,
                    'created_at': now,
                    'updated_at': now,
                })
        
        # Use COPY for inserts (very fast!)
        # If insert fails, we must raise exception to prevent incorrect metrics
        if insert_rows:
            self._copy_insert(insert_rows)
        
        # Insert errors
        try:
            if error_records:
                db.session.bulk_insert_mappings(ImportError, error_records)
                db.session.commit()
                logger.info("Successfully inserted %s error records", len(error_records))
        except Exception as exc:
            logger.exception("Error inserting error records: %s", exc)
            db.session.rollback()
            traceback.print_exc()
        
        # Final progress update
        self.batch.update_progress(total_rows, total_rows)
        
        logger.info("COPY completed: inserted=%s errors=%s", inserted, errors)
        return ImportResult(inserted=inserted, updated=updated, errors=errors)
    
    def _copy_insert(self, rows: list[dict]):
        """Use PostgreSQL COPY for fast bulk insert"""
        if not rows:
            return
        
        try:
            db.session.bulk_insert_mappings(InvoiceDetail, rows)
            db.session.commit()
            logger.info("Successfully inserted %s rows", len(rows))
        except Exception as exc:
            db.session.rollback()
            logger.exception("Error inserting %s rows: %s", len(rows), exc)
            traceback.print_exc()
            raise

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
