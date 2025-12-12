"""Read Excel file columns."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

file_path = project_root / 'data' / 'contractors-1.xlsx'
df = pd.read_excel(file_path, nrows=0)

print("Columns in contractors-1.xlsx:")
for i, col in enumerate(df.columns, 1):
    print(f"{i}. {col}")

print(f"\nTotal columns: {len(df.columns)}")

