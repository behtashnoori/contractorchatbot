from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd
from werkzeug.datastructures import FileStorage

from ..extensions import db
from ..models import Contractor, ImportBatch, ImportError, User
from .import_activation import (
    deactivate_active_rows,
    mark_batch_published,
    mark_previous_active_replaced,
)
from .import_utils import (
    normalize_code,
    normalize_str,
    row_payload_from_series,
)

logger = logging.getLogger(__name__)

EXPECTED_COLUMNS = [
    "کد تامین کننده",
    "نام تامین کننده",
    "وضعیت",
    "نوع",
    "کد تفصیلی",
]


@dataclass
class ImportResult:
    inserted: int
    updated: int
    errors: int


class CodTafsiltaminImporter:
    """Importer for codtafsiltamin Excel files containing contractor directory."""

    def __init__(self, batch: ImportBatch):
        self.batch = batch

    def run(self, file_obj: FileStorage) -> ImportResult:
        try:
            # Read Excel file
            # We don't use dtype=str for all columns because we need to handle numeric codes properly
            dataframe = pd.read_excel(file_obj)
        except Exception as exc:  # pragma: no cover - pandas raises many subclasses
            raise ValueError(f"خطا در خواندن فایل اکسل: {str(exc)}") from exc

        self._validate_headers(dataframe)
        contractors, error_records = self._preflight_rows(dataframe)
        if not contractors:
            raise ValueError("codtafsiltamin import has no valid contractor rows.")
        return self._publish_preflight_rows(contractors, error_records)

    def _publish_preflight_rows(
        self,
        contractors: list[Contractor],
        error_records: list[ImportError],
    ) -> ImportResult:
        try:
            logger.info("codtafsiltamin import: publishing preflighted rows in one transaction")
            previous_contractors_by_detail = {
                contractor.detail_code: contractor.id
                for contractor in Contractor.query.filter(Contractor.is_active.is_(True)).all()
            }
            mark_previous_active_replaced("codtafsiltamin", self.batch)
            deactivate_active_rows("codtafsiltamin")

            for contractor in contractors:
                contractor.last_update_batch_id = self.batch.id
                contractor.is_active = True
                db.session.add(contractor)
            db.session.flush()
            for contractor in contractors:
                previous_id = previous_contractors_by_detail.get(contractor.detail_code)
                if previous_id:
                    User.query.filter_by(contractor_id=previous_id).update(
                        {User.contractor_id: contractor.id},
                        synchronize_session=False,
                    )
            for error_record in error_records:
                db.session.add(error_record)

            total_rows = len(contractors) + len(error_records)
            self.batch.total_rows = total_rows
            self.batch.rows_processed = total_rows
            self.batch.progress_percentage = 100.0 if total_rows else 0.0
            mark_batch_published(self.batch)

            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception("codtafsiltamin publish failed; transaction rolled back")
            raise

        return ImportResult(inserted=len(contractors), updated=0, errors=len(error_records))

    def _preflight_rows(self, dataframe: pd.DataFrame) -> tuple[list[Contractor], list[ImportError]]:
        contractors: list[Contractor] = []
        error_records: list[ImportError] = []
        seen_detail_codes: set[str] = set()

        for index, row in dataframe.iterrows():
            try:
                contractor = self._create_contractor(row)
                if contractor.detail_code in seen_detail_codes:
                    raise ValueError(f"Duplicate detail_code in import file: {contractor.detail_code}")
                seen_detail_codes.add(contractor.detail_code)
                contractors.append(contractor)
            except Exception as exc:
                error_records.append(
                    ImportError(
                        batch_id=self.batch.id,
                        source_file="codtafsiltamin",
                        row_index=int(index) + 2,
                        message=str(exc)[:255],
                        payload=row_payload_from_series(row),
                    )
                )

        return contractors, error_records

    def _validate_headers(self, frame: pd.DataFrame) -> None:
        # Normalize both dataframe columns and expected columns for comparison
        frame_cols_normalized = {normalize_str(str(col)) or str(col).strip(): col for col in frame.columns}
        missing = []
        for expected in EXPECTED_COLUMNS:
            expected_normalized = normalize_str(expected) or expected.strip()
            if expected_normalized not in frame_cols_normalized:
                missing.append(expected)
        if missing:
            raise ValueError(f"ستون های زیر در فایل یافت نشدند: {', '.join(missing)}")

    def _create_contractor(self, row: pd.Series) -> Contractor:
        detail_code = normalize_code(row.get("کد تفصیلی"))
        supplier_code = normalize_code(row.get("کد تامین کننده"))
        
        # If detail_code is empty, use supplier_code as fallback
        if not detail_code:
            if not supplier_code:
                raise ValueError("کد تفصیلی و کد تامین کننده هر دو خالی هستند")
            detail_code = supplier_code

        contractor = Contractor(
            detail_code=detail_code,
            supplier_code=supplier_code,
            name=normalize_str(row.get("نام تامین کننده")) or "نامشخص",
            status=normalize_str(row.get("وضعیت")) or "نامشخص",
            type=normalize_str(row.get("نوع")),
            raw_payload=row_payload_from_series(row),
        )

        return contractor
