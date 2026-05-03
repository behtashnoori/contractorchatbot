import csv
import functools
import io
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request

from .db import get_conn
from .queries import fetch_kpi_yearly

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _expected_kpi_key() -> str:
	return os.getenv("KPI_API_KEY", "").strip()


def _kpi_key_authorized() -> bool:
	expected = _expected_kpi_key()
	if not expected:
		return False
	auth = request.headers.get("Authorization") or ""
	bearer = ""
	if auth.lower().startswith("bearer "):
		bearer = auth[7:].strip()
	x_key = (request.headers.get("X-API-Key") or "").strip()
	q_key = (request.args.get("api_key") or "").strip()
	return bearer == expected or x_key == expected or q_key == expected


def require_kpi_api_key(view_func):
	"""Require KPI_API_KEY via Bearer, X-API-Key, or (for GET /kpi only) api_key query."""

	@functools.wraps(view_func)
	def wrapped(*args, **kwargs):
		expected = _expected_kpi_key()
		if not expected:
			return jsonify({"error": "service_unconfigured"}), 503
		if not _kpi_key_authorized():
			return jsonify({"error": "unauthorized"}), 401
		return view_func(*args, **kwargs)

	return wrapped


def create_app() -> Flask:
	app = Flask(__name__)

	@app.get("/api/health")
	def health():
		return jsonify({"status": "ok"})

	@app.get("/api/kpi/yearly")
	@require_kpi_api_key
	def kpi_yearly():
		supplier_uid = request.args.get("supplier_uid")
		supplier_name = request.args.get("supplier_name")
		source = request.args.get("source", "all")
		year = request.args.get("year")
		limit = int(request.args.get("limit", "1000"))
		offset = int(request.args.get("offset", "0"))

		if not supplier_uid and not supplier_name:
			return jsonify({"error": "supplier_uid or supplier_name is required"}), 400

		with get_conn() as conn:
			rows = fetch_kpi_yearly(
				conn=conn,
				supplier_uid=supplier_uid,
				supplier_name=supplier_name,
				source=source,
				year=year,
				limit=limit,
				offset=offset,
			)
		return jsonify(rows)

	@app.get("/api/kpi/yearly/export")
	@require_kpi_api_key
	def export_kpi_yearly():
		supplier_uid = request.args.get("supplier_uid")
		supplier_name = request.args.get("supplier_name")
		source = request.args.get("source", "all")
		year = request.args.get("year")
		export_format = request.args.get("format", "csv").lower()

		if not supplier_uid and not supplier_name:
			return jsonify({"error": "supplier_uid or supplier_name is required"}), 400

		with get_conn() as conn:
			rows = fetch_kpi_yearly(
				conn=conn,
				supplier_uid=supplier_uid,
				supplier_name=supplier_name,
				source=source,
				year=year,
				limit=100000,
				offset=0,
			)

		if export_format == "xlsx":
			df = pd.DataFrame(rows)
			buf = io.BytesIO()
			with pd.ExcelWriter(buf, engine="openpyxl") as writer:
				df.to_excel(writer, index=False, sheet_name="kpi")
			buf.seek(0)
			return Response(
				buf.getvalue(),
				mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
				headers={"Content-Disposition": "attachment; filename=kpi.xlsx"},
			)

		sio = io.StringIO()
		writer = csv.DictWriter(
			sio,
			fieldnames=list(rows[0].keys())
			if rows
			else [
				"source",
				"customer_uid",
				"supplier_name",
				"year_j",
				"status",
				"count",
				"amount_a",
				"amount_b",
			],
		)
		writer.writeheader()
		for r in rows:
			writer.writerow(r)
		data = ("\ufeff" + sio.getvalue()).encode("utf-8")
		return Response(
			data,
			mimetype="text/csv; charset=utf-8",
			headers={"Content-Disposition": "attachment; filename=kpi.csv"},
		)

	@app.get("/")
	def index():
		return render_template("index.html")

	@app.get("/kpi")
	@require_kpi_api_key
	def kpi_page():
		supplier_uid = request.args.get("supplier_uid")
		supplier_name = request.args.get("supplier_name")
		source = request.args.get("source", "all")
		year = request.args.get("year")
		rows = []
		if supplier_uid or supplier_name:
			with get_conn() as conn:
				rows = fetch_kpi_yearly(
					conn, supplier_uid, supplier_name, source, year, 1000, 0
				)
		return render_template(
			"kpi.html",
			rows=rows,
			q={
				"supplier_uid": supplier_uid or "",
				"supplier_name": supplier_name or "",
				"source": source,
				"year": year or "",
			},
		)

	return app


app = create_app()
