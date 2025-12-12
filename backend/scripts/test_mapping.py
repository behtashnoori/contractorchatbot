"""Test header mapping for contractors-1."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from backend.app.services.contractors_one_importer import ContractorsOneImporter, HEADER_RULES
from backend.app.models import ImportBatch
from backend.app import create_app
from backend.app.extensions import db

app = create_app()
with app.app_context():
    # Create a dummy batch
    batch = ImportBatch(
        name="test",
        source="contractors-1",
        status="processing",
    )
    db.session.add(batch)
    db.session.flush()
    
    importer = ContractorsOneImporter(batch)
    
    # Read Excel file
    df = pd.read_excel('data/contractors-1.xlsx', nrows=0)
    
    # Test mapping
    column_map = importer._map_headers(df.columns)
    
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("Mapped columns:")
    for key, original_col in column_map.items():
        print(f"  {key} -> {original_col}")
    
    print(f"\nTotal mapped: {len(column_map)}")
    print(f"Total rules: {len(HEADER_RULES)}")
    
    # Check required keys
    required = ["cover_number", "invoice_status"]
    missing = [key for key in required if key not in column_map]
    if missing:
        print(f"\nMissing required keys: {missing}")
    else:
        print("\nAll required keys found!")
    
    # Show all columns
    print("\nAll columns in Excel:")
    for i, col in enumerate(df.columns, 1):
        normalized = normalize_str(str(col)) or str(col).strip()
        print(f"{i}. {col} -> normalized: {normalized}")

