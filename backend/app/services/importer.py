from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..extensions import db
from ..models import Contractor, ImportBatch, ImportError, InvoiceDetail, InvoiceSummary


@dataclass
class ImportResult:
    inserted: int
    updated: int
    errors: int


class ExcelImporter:
    """Placeholder importer orchestrating Excel ingestion."""

    def __init__(self, batch: ImportBatch):
        self.batch = batch

    def run(self, cod_detail: Path, surface: Path, details: Path) -> ImportResult:
        # NOTE: Implement parsing logic using pandas/openpyxl here.
        # Current implementation stores placeholders only.
        self.batch.status = "completed"
        db.session.commit()
        return ImportResult(inserted=0, updated=0, errors=0)

