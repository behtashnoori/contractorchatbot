## Flask KPI API

### Setup
```bash
python -m venv .venv
.venv\Scripts\pip install -r api/requirements.txt

set PGHOST=localhost
set PGPORT=5432
set PGUSER=postgres
set PGPASSWORD=bagheri13
set PGDATABASE=contractor_portal

set FLASK_APP=api/app.py
.venv\Scripts\python -m flask run --port 5001
```

### Endpoints
- `GET /api/health` → `{status: "ok"}`
- `GET /api/kpi/yearly`
  - Query params: `supplier_uid` or `supplier_name`, optional `source` (`invoices|contractors2|all`), optional `year`, `limit`, `offset`.
 - `GET /api/kpi/yearly/export` with same params + `format=csv|xlsx`

### UI
- Open `http://localhost:5001/` → فرم جست‌وجو
- صفحه `http://localhost:5001/kpi` نتیجه را نمایش می‌دهد و لینک دانلود CSV/XLSX دارد.

Examples:
```bash
curl "http://localhost:5001/api/kpi/yearly?supplier_uid=732-0026968"
curl "http://localhost:5001/api/kpi/yearly?supplier_name=سیاهش ایوبی (تعمیر)"
curl "http://localhost:5001/api/kpi/yearly?supplier_uid=732-0026968&source=invoices&year=1404"

# export
curl -OJ "http://localhost:5001/api/kpi/yearly/export?supplier_uid=732-0026968&format=csv"
```


