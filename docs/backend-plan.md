## Database Schema Design

- **contractors**: stores contractor identity from `codtafsiltamin.xlsx`.
  - `id` (uuid, pk)
  - `detail_code` (`کد تفصیلی`, unique, indexed)
  - `supplier_code` (`کد تامین کننده`, nullable, indexed)
  - `name` (`نام تامین کننده`)
  - `status` (`وضعیت`)
  - `type` (`نوع`)
  - `relationship_start` (`تاریخ شروع ارتباط`, date)
  - `raw_payload` (jsonb) – original row for traceability
  - `created_at` / `updated_at` timestamps

- **invoices_summary**: rows from `contractors-1.xlsx` (روکش‌های بازرگانی).
  - `id` (uuid, pk)
  - `detail_code` (fk → contractors.detail_code, nullable)
  - `supplier_code`
  - `automation_number` (`شماره اتوماسیون`)
  - `invoice_created_at` (`تاريخ ایجاد سند حسابداری فاکتور`)
  - `delivered_to_accounting_at` (`تاریخ تحویل به حسابداری`)
  - `delivered_to_supervisor_at` (`تاریخ تحویل به ناظر`)
  - `invoice_date` (`تاريخ ایجاد فاکتور`)
  - `cover_number` (`شماره روکش`)
  - `business_owner` (`بهره بردار`)
  - `cost_subject` (`موضوع هزینه فاکتور خرید`)
  - `gross_amount` (`مبلغ کل`)
  - `net_amount` (`مبلغ بدون مالیات`)
  - `time_span` (`محدوده زمانی انجام کار`)
  - `invoice_status` (`وضعیت فاکتور`)
  - `notes` (`توضیحات فاکتور خرید`)
  - `contractor_invoice_no` (`شماره صورت حساب پیمانکار فاکتور خرید`)
  - `permit_number` (`شماره مجوز فاکتور خرید`)
  - `permit_type` (`نوع مجوز فاکتور خرید`)
  - `client_contract_number` (`شماره قرارداد کارفرما فاکتور خرید`)
  - `client_name` (`نام کارفرما`)
  - `raw_payload` (jsonb)
  - `created_at` / `updated_at`

- **invoices_detail**: entries from `contractors-2.xlsx` (ثبت‌های مالی).
  - `id` (uuid, pk)
  - `detail_code`
  - `supplier_code`
  - `invoice_no` (`شماره`)
  - `invoice_date` (`تاریخ`)
  - `unit_code` (`واحد/رمز تامین`)
  - `supplier_name` (`تامین کننده`)
  - `status` (`وضعیت`)
  - `item_title` (`عنوان قلم خریدنی`)
  - `gross_amount` (`مبلغ ناخالص`)
  - `reference` (`مبنا`)
  - `description` (`توضیحات`)
  - `raw_payload` (jsonb)
  - `created_at` / `updated_at`

- **users**: generated contractor accounts.
  - `id` (uuid, pk)
  - `username` (unique, derived from `detail_code`)
  - `password_hash`
  - `contractor_id` (fk)
  - `last_login_at`
  - audit timestamps

Indexes:
- B-tree on `drivers.detail_code`, `invoices_summary.detail_code`, `invoices_detail.detail_code` for efficient joins.
- Partial index on `users.contractor_id` to enforce one account per contractor.

## Data Flow & Ingestion

1. **Upload**: Commercial expert uploads Excel files through admin UI (to be implemented) or CLI.
2. **Landing Zone**: Files stored under `uploads/{timestamp}/`.
3. **Parsing Jobs**:
   - Use `pandas` or `openpyxl` to read primary sheet.
   - Normalize column names (convert to snake_case, drop whitespace).
   - Clean dates (convert Persian `yyyy/mm/dd` to Gregorian with `khayyam` or custom parser).
   - Map boolean/status fields to enums.
4. **Staging Tables** (optional) to keep raw rows before merge.
5. **Deduplication & Merge**:
   - Contractors keyed by `detail_code`; update existing rows keeping latest non-null fields.
   - Invoice summary keyed by combination (`cover_number`, `automation_number`).
   - Invoice details keyed by (`invoice_no`, `reference`).
6. **Audit**:
   - Track upload batch id, filename, processed_at, row counts, and errors in `import_batches` table.
   - Persist rejection reasons per row in `import_errors`.

## Authentication Strategy

- Generate username/password per contractor at import time:
  - `username = f\"ct-{detail_code}\"`.
  - Password randomly generated, stored hashed (Argon2id with `argon2-cffi`).
  - Export onboarding CSV for distribution to contractors.
- Login flow:
  - Contractors submit username/password.
  - Flask verifies hash, issues JWT access token (15 min) + refresh (7 days).
  - Use Flask extensions: `flask-jwt-extended`, `flask-bcrypt` or `argon2`.

## API Endpoints

- `POST /auth/login`: contractor login, returns tokens.
- `POST /auth/refresh`: renew access token.
- `GET /me`: contractor profile (name, status).
- `GET /invoices`: list invoices merging summary + detail.
  - Query params: `status`, `from_date`, `to_date`, `search`.
  - Response includes aggregated amounts, cover number, statuses.
- `GET /invoices/<cover_number>`: detail with joined summary row plus related detail rows.
- Admin endpoints (future): upload status, batch history.

## Technology Stack

- Flask + SQLAlchemy + Alembic for migrations.
- PostgreSQL preferred (JSONB support); fallback SQLite for dev.
- Celery (optional) for async imports if files become large; otherwise synchronous job with progress feedback.

## Outstanding Questions

- Confirm timezone/calendar expectations for dates (convert to Gregorian or keep Jalali?).
- Establish retention policy and purge strategy for old batches.







