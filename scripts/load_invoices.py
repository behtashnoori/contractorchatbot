import os
import sys
import uuid
from datetime import datetime

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values


def _required_env(name: str) -> str:
	value = os.getenv(name)
	if not value:
		raise RuntimeError(f"{name} must be set in the environment.")
	return value


def normalize_column_name(col: str) -> str:
	col = str(col).strip().replace("\u200c", "")  # remove ZWNJ
	mapping = {
		"تامین کننده": "supplier_name",
		"نام تامین کننده": "supplier_name",
		"شماره روکش": "request_no",
		"بهره بردار": "beneficiary",
		"حوزه": "department",
		"وضعیت": "status",
		"نوع هزینه فاکتور": "invoice_cost_type",
		"مبلغ بدون مالیات بر ارزش افزوده": "amount_wo_tax",
		"مبلغ کل": "total_amount",
		"تاریخ ایجاد فاکتور": "created_at_jalali",
		"تاریخ تحویل به حسابداری": "delivered_to_acc_j",
		"در اختیار ناظر": "in_observer_j",
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
		"supplier_name",
		"request_no",
		"beneficiary",
		"department",
		"status",
		"invoice_cost_type",
		"amount_wo_tax",
		"total_amount",
		"created_at_jalali",
		"delivered_to_acc_j",
		"in_observer_j",
	]
	for c in cols:
		if c not in df.columns:
			df[c] = None

	# cleanup
	for c in cols:
		df[c] = df[c].astype("string").str.strip()

	# convert amounts to numeric safely; leave None on failure
	for c in ["amount_wo_tax", "total_amount"]:
		df[c] = pd.to_numeric(df[c].str.replace(",", ""), errors="coerce")

	return df[cols]


def insert_staging(df: pd.DataFrame, source_filename: str) -> int:
	conn = psycopg2.connect(
		host=os.getenv("PGHOST", "localhost"),
		port=int(os.getenv("PGPORT", "5432")),
		user=os.getenv("PGUSER", "postgres"),
		password=_required_env("PGPASSWORD"),
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
				r["supplier_name"],
				r["request_no"],
				r["beneficiary"],
				r["department"],
				r["status"],
				r["invoice_cost_type"],
				None if pd.isna(r["amount_wo_tax"]) else float(r["amount_wo_tax"]),
				None if pd.isna(r["total_amount"]) else float(r["total_amount"]),
				r["created_at_jalali"],
				r["delivered_to_acc_j"],
				r["in_observer_j"],
				None,  # other_cols_json
			)
		)

	with conn, conn.cursor() as cur:
		sql = """
			INSERT INTO landing.invoices_stage (
				batch_id, source_filename, ingested_at,
				supplier_name, request_no, beneficiary, department, status, invoice_cost_type,
				amount_wo_tax, total_amount, created_at_jalali, delivered_to_acc_j, in_observer_j,
				other_cols_json
			) VALUES %s
		"""
		execute_values(cur, sql, rows, page_size=1000)

	conn.close()
	return len(rows)


def main():
	if len(sys.argv) < 2:
		print("Usage: python scripts/load_invoices.py <path-to-excel-or-csv>")
		sys.exit(1)

	path = sys.argv[1]
	df = read_input(path)
	count = insert_staging(df, os.path.basename(path))
	print(f"Inserted {count} rows into landing.invoices_stage.")


if __name__ == "__main__":
	main()






