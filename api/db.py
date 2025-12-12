import os
import psycopg2


def get_conn():
	return psycopg2.connect(
		host=os.getenv("PGHOST", "localhost"),
		port=int(os.getenv("PGPORT", "5432")),
		user=os.getenv("PGUSER", "postgres"),
		password=os.getenv("PGPASSWORD", "bagheri13"),
		dbname=os.getenv("PGDATABASE", "contractor_portal"),
	)






