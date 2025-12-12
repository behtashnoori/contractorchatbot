from __future__ import annotations

from dataclasses import dataclass
import pandas as pd
from werkzeug.datastructures import FileStorage

from ..extensions import db
from ..models import Contractor, ImportBatch, ImportError
from .import_utils import (
    normalize_code,
    normalize_str,
    row_payload_from_series,
)

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

        # Delete all existing data before importing new data
        print(f"[CodTafsiltaminImporter] Deleting existing data...")
        
        # First, delete all Contractor records (they may have dependent records, but FK is nullable)
        deleted_contractors = db.session.query(Contractor).delete()
        print(f"[CodTafsiltaminImporter] Deleted {deleted_contractors} existing Contractor records")
        
        # Then delete ImportError records for codtafsiltamin batches (excluding current batch)
        codtafsiltamin_batch_ids = [
            batch.id for batch in ImportBatch.query.filter_by(source="codtafsiltamin").all()
            if batch.id != self.batch.id  # Exclude current batch
        ]
        if codtafsiltamin_batch_ids:
            deleted_errors = ImportError.query.filter(ImportError.batch_id.in_(codtafsiltamin_batch_ids)).delete()
            print(f"[CodTafsiltaminImporter] Deleted {deleted_errors} ImportError records")
        
        # Finally delete ImportBatch records (excluding current batch)
        deleted_batches = ImportBatch.query.filter(
            ImportBatch.source == "codtafsiltamin",
            ImportBatch.id != self.batch.id  # Exclude current batch
        ).delete()
        print(f"[CodTafsiltaminImporter] Deleted {deleted_batches} ImportBatch records")
        
        db.session.commit()

        inserted, updated, errors = 0, 0, 0

        for index, row in dataframe.iterrows():
            try:
                contractor = self._create_contractor(row)
                db.session.add(contractor)
                inserted += 1
            except Exception as exc:  # pragma: no cover - defensive
                errors += 1
                db.session.add(
                    ImportError(
                        batch_id=self.batch.id,
                        source_file="codtafsiltamin",
                        row_index=int(index) + 2,  # +2 for header + 1-index
                        message=str(exc),
                        payload=row_payload_from_series(row),
                    )
                )

        db.session.commit()
        return ImportResult(inserted=inserted, updated=updated, errors=errors)

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
            last_update_batch_id=self.batch.id,
        )

        return contractor

