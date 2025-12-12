import os
import sys
import uuid
from datetime import datetime

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values


def normalize_column_name(col: str) -> str:
	"""Map Persian headers to internal names."""
	col = str(col).strip().replace("\u200c", "")  # remove zero-width non-joiner
	mapping = {
		"کد تامین کننده": "supplier_code",
		"نام تامین کننده": "supplier_name",
		"وضعیت": "status",
		"نوع": "type",
		"تاریخ شروع ارتباط": "start_date_jalali",
		"کد تفصیلی": "tafsili_code",
	}
	return mapping.get(col, col)


def read_input(path: str) -> pd.DataFrame:
	ext = os.path.splitext(path)[1].lower()
	if ext in [".xlsx", ".xls"]:
		df = pd.read_excel(path, dtype=str)
	elif ext in [".csv", ".txt"]:
		df = pd.read_csv(path, dtype=str)
	else:
		raise ValueError(f"Unsupported file type: {ext}")

	# rename columns
	df = df.rename(columns={c: normalize_column_name(c) for c in df.columns})
	# keep only known columns
	cols = [
		"supplier_code",
		"supplier_name",
		"status",
		"type",
		"start_date_jalali",
		"tafsili_code",
	]
	for c in cols:
		if c not in df.columns:
			df[c] = None

	# trim strings
	for c in cols:
		df[c] = df[c].astype("string").str.strip()

	return df[cols]


def insert_staging(df: pd.DataFrame, source_filename: str) -> int:
	conn = psycopg2.connect(
		host=os.getenv("PGHOST", "localhost"),
		port=int(os.getenv("PGPORT", "5432")),
		user=os.getenv("PGUSER", "postgres"),
		password=os.getenv("PGPASSWORD", "bagheri13"),
		dbname=os.getenv("PGDATABASE", "contractor_portal"),
	)
	conn.autocommit = True

	batch_id = str(uuid.uuid4())
	now = datetime.utcnow()

	rows = []
	for _, r in df.iterrows():
		rows.append(
			(
				batch_id,
				source_filename,
				now,
				r["supplier_code"],
				r["supplier_name"],
				r["status"],
				r["type"],
				r["start_date_jalali"],
				r["tafsili_code"],
			)
		)

	with conn, conn.cursor() as cur:
		sql = """
			INSERT INTO landing.codtafsiltamin_stage (
				batch_id, source_filename, ingested_at,
				supplier_code, supplier_name, status, type, start_date_jalali, tafsili_code
			) VALUES %s
		"""
		execute_values(cur, sql, rows, page_size=1000)

	conn.close()
	return len(rows)


def main():
	if len(sys.argv) < 2:
		print("Usage: python scripts/load_codtafsiltamin.py <path-to-excel-or-csv>")
		sys.exit(1)

	path = sys.argv[1]
	df = read_input(path)
	count = insert_staging(df, os.path.basename(path))
	print(f"Inserted {count} rows into staging.")


if __name__ == "__main__":
	main()


