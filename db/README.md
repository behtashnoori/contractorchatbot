## codtafsiltamin setup (single DB: `contractor_portal`)

This folder contains SQL schemas and utilities to ingest the file containing supplier accounts (`codtafsiltamin`) and build a normalized core table with a unique customer UID based on the composite key `(supplier_code, tafsili_code)`.

### 1) Create database (if it does not exist)
Create a PostgreSQL database named `contractor_portal`. Then run both schemas in that DB:

```sql
\i db/sql/staging_schema.sql
\i db/sql/core_schema.sql
```

> We use two schemas (`landing`, `public`) inside the single database `contractor_portal`.

### 2) Install loader dependencies

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 3) Configure database connection for loader
Set env vars. Do not commit real credentials; keep them only in your local environment or secret manager:

```bash
set PGHOST=<DB_HOST>
set PGPORT=<DB_PORT>
set PGUSER=<DB_USER>
set PGPASSWORD=<DB_PASSWORD>
set PGDATABASE=<DB_NAME>
```

### 4) Load your Excel/CSV into staging

```bash
.venv\Scripts\python scripts\load_codtafsiltamin.py D:\path\to\codtafsiltamin.xlsx

# file 2 (invoices)
.venv\Scripts\python scripts\load_invoices.py D:\path\to\invoices.xlsx

# file 3 (contractors-2)
.venv\Scripts\python scripts\load_contractors2.py D:\path\to\contractors-2.xlsx
```

The loader expects headers (Persian) like:
- کد تامین کننده
- نام تامین کننده
- وضعیت
- نوع
- تاریخ شروع ارتباط
- کد تفصیلی

### 5) Upsert to core
Run in the same `contractor_portal` DB:

```sql
\i db/sql/upsert_codtafsiltamin.sql
\i db/sql/upsert_invoices.sql
\i db/sql/upsert_contractors2.sql
```

This will populate `public.dim_supplier_account` where:
- `customer_uid = supplier_code || '-' || tafsili_code`
- Unique constraints ensure idempotent updates.

### 6) Quality checks and quick reports

```sql
\i db/sql/quality_checks.sql
```

### Notes on dates
We store the original Jalali date text in `start_date_jalali` and optionally a Gregorian `start_date`. A conversion function can be added later if required.

## Strong supplier name resolution
We added:
- `public.normalize_persian(text)` immutable function for Persian cleanup (ی/ک عربی→ایرانی، حذف نیم‌فاصله/علائم، فشرده‌سازی فاصله‌ها).
- `supplier_name_norm` on `public.dim_supplier_account` (stored, indexed).
- `public.supplier_aliases` for نگاشت املاهای متفاوت به `customer_uid`.

The upsert for invoices resolves order:
1) Alias match (`supplier_aliases.alias_norm`).
2) Direct normalized match to `dim_supplier_account.supplier_name_norm`.

### Managing aliases
Insert an alias when a supplier name in invoices doesn't match directly:

```sql
INSERT INTO public.supplier_aliases (alias_name, customer_uid, source_note)
VALUES (N'سیــاوش ایوبی (تعمیر)', '732-0026968', 'manual mapping');
```

Then re-run:

```sql
\i db/sql/upsert_invoices.sql
```

### Fuzzy suggestions (optional)
We enabled `pg_trgm`. To find likely matches for unknown names:

```sql
WITH unknown AS (
  SELECT DISTINCT supplier_name_raw
  FROM public.fact_invoices
  WHERE customer_uid IS NULL
)
SELECT u.supplier_name_raw,
       dsa.supplier_name,
       similarity(public.normalize_persian(u.supplier_name_raw), dsa.supplier_name_norm) AS sim
FROM unknown u
JOIN public.dim_supplier_account dsa
  ON public.normalize_persian(u.supplier_name_raw) % dsa.supplier_name_norm
ORDER BY sim DESC
LIMIT 100;
```

Pick the correct target and add to `supplier_aliases` to lock it in.

## Replace-load flow (manual uploads)
Each upload should replace previous data of that file:

1) File 1 (codtafsiltamin)

```sql
\i db/sql/load_replace_codtafsiltamin.sql   -- truncates landing + dim
-- run loader:
-- .venv\Scripts\python scripts\load_codtafsiltamin.py D:\path\to\codtafsiltamin.xlsx
\i db/sql/upsert_codtafsiltamin.sql
```

2) File 2 (invoices)

```sql
\i db/sql/load_replace_invoices.sql         -- truncates landing + fact
-- .venv\Scripts\python scripts\load_invoices.py D:\path\to\invoices.xlsx
\i db/sql/upsert_invoices.sql
```

3) File 3 (contractors-2)

```sql
\i db/sql/load_replace_contractors2.sql     -- truncates landing + fact
-- .venv\Scripts\python scripts\load_contractors2.py D:\path\to\contractors-2.xlsx
\i db/sql/upsert_contractors2.sql
```

4) File 1 (covers/روکش)

```sql
\i db/sql/load_replace_covers.sql           -- truncates landing + dim_cover
-- .venv\Scripts\python scripts\load_covers.py D:\path\to\covers.xlsx
\i db/sql/upsert_covers.sql
```

## KPI Views
Run once to create views:

```sql
\i db/sql/views_kpi.sql
```

Examples:

```sql
-- by supplier name
\i db/sql/reports_examples.sql
```
