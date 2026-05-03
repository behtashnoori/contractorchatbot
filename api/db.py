import os

import psycopg2


def get_conn():
	password = os.environ.get("PGPASSWORD")
	if not password:
		raise RuntimeError("PGPASSWORD must be set for KPI database connections.")
	return psycopg2.connect(
		host=os.getenv("PGHOST", "localhost"),
		port=int(os.getenv("PGPORT", "5432")),
		user=os.getenv("PGUSER", "postgres"),
		password=password,
		dbname=os.getenv("PGDATABASE", "contractor_portal"),
	)
