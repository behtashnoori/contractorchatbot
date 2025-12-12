from flask import Flask, request, jsonify
from .db import get_conn
from .queries import fetch_kpi_yearly
import io
import csv
import pandas as pd
from flask import Response, render_template, redirect, url_for


def create_app() -> Flask:
	app = Flask(__name__)

	@app.get("/api/health")
	def health():
		return jsonify({"status": "ok"})

	@app.get("/api/kpi/yearly")
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

		# default CSV with UTF-8 BOM (Excel-friendly)
		sio = io.StringIO()
		writer = csv.DictWriter(sio, fieldnames=list(rows[0].keys()) if rows else
			["source","customer_uid","supplier_name","year_j","status","count","amount_a","amount_b"])
		writer.writeheader()
		for r in rows:
			writer.writerow(r)
		data = ("\ufeff" + sio.getvalue()).encode("utf-8")
		return Response(
			data,
			mimetype="text/csv; charset=utf-8",
			headers={"Content-Disposition": "attachment; filename=kpi.csv"},
		)

	# -------- UI --------
	@app.get("/")
	def index():
		return render_template("index.html")

	@app.get("/kpi")
	def kpi_page():
		supplier_uid = request.args.get("supplier_uid")
		supplier_name = request.args.get("supplier_name")
		source = request.args.get("source", "all")
		year = request.args.get("year")
		rows = []
		if supplier_uid or supplier_name:
			with get_conn() as conn:
				rows = fetch_kpi_yearly(conn, supplier_uid, supplier_name, source, year, 1000, 0)
		return render_template("kpi.html", rows=rows, q={
			"supplier_uid": supplier_uid or "",
			"supplier_name": supplier_name or "",
			"source": source,
			"year": year or ""
		})

	return app


app = create_app()


