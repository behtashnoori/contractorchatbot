import os
import sys
import uuid
from datetime import datetime

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values


def normalize_column_name(col: str) -> str:
	col = str(col).strip().replace("\u200c", "")
	mapping = {
		"شماره": "doc_no",
		"تاریخ": "doc_date_jalali",
		"واحد/رمز تامین": "unit_or_code",
		"تامین کننده": "supplier_name",
		"وضعیت": "status",
		"عنوان قلم خرید": "item_title",
		"مبلغ ناخالص": "gross_amount",
		"مبنا": "basis",
		"توضیحات": "description",
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

	df = df.rename(columns={c: normalize_column_name(c) for c in df.columns})

	cols = [
		"doc_no",
		"doc_date_jalali",
		"unit_or_code",
		"supplier_name",
		"status",
		"item_title",
		"gross_amount",
		"basis",
		"description",
	]
	for c in cols:
		if c not in df.columns:
			df[c] = None

	for c in cols:
		df[c] = df[c].astype("string").str.strip()

	df["gross_amount"] = pd.to_numeric(df["gross_amount"].str.replace(",", ""), errors="coerce")

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
				r["doc_no"],
				r["doc_date_jalali"],
				r["unit_or_code"],
				r["supplier_name"],
				r["status"],
				r["item_title"],
				None if pd.isna(r["gross_amount"]) else float(r["gross_amount"]),
				r["basis"],
				r["description"],
			)
		)

	with conn, conn.cursor() as cur:
		sql = """
			INSERT INTO landing.contractors2_stage (
				batch_id, source_filename, ingested_at,
				doc_no, doc_date_jalali, unit_or_code, supplier_name, status,
				item_title, gross_amount, basis, description
			) VALUES %s
		"""
		execute_values(cur, sql, rows, page_size=1000)

	conn.close()
	return len(rows)


def main():
	if len(sys.argv) < 2:
		print("Usage: python scripts/load_contractors2.py <path-to-excel-or-csv>")
		sys.exit(1)

	path = sys.argv[1]
	df = read_input(path)
	count = insert_staging(df, os.path.basename(path))
	print(f"Inserted {count} rows into landing.contractors2_stage.")


if __name__ == "__main__":
	main()






