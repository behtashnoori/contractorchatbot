from __future__ import annotations

import pandas as pd

from app.models import ImportBatch
from app.services.codtafsiltamin_importer import (
    CodTafsiltaminImporter,
    EXPECTED_COLUMNS,
)


def test_create_contractor_matches_current_model_fields():
    batch = ImportBatch(name="pytest-cod", source="codtafsiltamin", status="pending")
    importer = CodTafsiltaminImporter(batch)
    row = pd.Series(
        {
            EXPECTED_COLUMNS[0]: 732,
            EXPECTED_COLUMNS[1]: "Test Supplier",
            EXPECTED_COLUMNS[2]: "active",
            EXPECTED_COLUMNS[3]: "internal",
            EXPECTED_COLUMNS[4]: "0026968",
        }
    )

    contractor = importer._create_contractor(row)

    assert contractor.detail_code == "0026968"
    assert contractor.supplier_code == "732"
    assert contractor.name == "Test Supplier"
    assert contractor.status == "active"
    assert contractor.type == "internal"
    assert EXPECTED_COLUMNS[0] in contractor.raw_payload
    assert contractor.last_update_batch_id is None
    assert contractor.is_active is None
