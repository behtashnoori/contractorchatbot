## Import Workflow

### 1. Upload Interface
- Admin-only page (`/admin/uploads`) accepts files for:
  - `codtafsiltamin.xlsx`
  - `contractors-1.xlsx`
  - `contractors-2.xlsx`
- Validation rules:
  - MIME type `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
  - Max size configurable (default 25 MB)
  - Required columns present (see schemas below)
  - Reject if template version mismatch (store expected hash of header row)

### 2. Staging Layout
- Save uploaded files to `uploads/<batch_id>/<original_name>`.
- Insert `import_batches` row with metadata:
  - `id`, `uploader_id`, `uploaded_at`, `status (pending/running/completed/failed)`
  - `notes`
- Spawn background job (Celery or `rq`) with batch id.

### 3. Parsing Steps

#### codtafsiltamin.xlsx
| Column | Description | Type | Required |
| --- | --- | --- | --- |
| `کد تامین کننده` | Supplier code | string | yes |
| `نام تامین کننده` | Contractor name | string | yes |
| `وضعیت` | Status (`فعال`, `غیرفعال`) | enum | yes |
| `نوع` | Internal/External | enum | yes |
| `تاریخ شروع ارتباط` | Jalali date | date | optional |
| `کد تفصیلی` | Detail code | string | yes |

#### contractors-1.xlsx
Key columns for join:
- `کد تفصیلی`
- `شماره روکش`
- `شماره اتوماسیون`

#### contractors-2.xlsx
Key columns:
- `کد تفصیلی`
- `شماره`
- `مبنا`

### 4. Transformation Rules
- Normalize column names with map → snake_case (e.g., `کد تفصیلی` → `detail_code`).
- Convert Jalali dates using `convertdate` or manual conversion; store both original and Gregorian.
- Strip commas from numeric strings and cast to decimal.
- Use consistent status enums:
  - Summary statuses: `['تاييد شده', 'در انتظار', 'رد شده']`.
  - Detail statuses: `['ثبت شده', 'معلق', 'ابطال']`.
- Trim whitespace, replace `-` or empty cells with `None`.

### 5. Load Strategies
- Use SQLAlchemy bulk upserts.
- Contractors:
  - upsert on `detail_code`.
  - Update status/type if changed, preserve earliest `relationship_start`.
- Invoices summary:
  - Upsert on `cover_number` + `automation_number`.
  - Maintain `last_update_batch_id`.
- Invoice detail:
  - Upsert on `invoice_no` + `reference`.

### 6. Error Handling
- Capture row-level errors: add to `import_errors(batch_id, source_file, row_index, message, payload_json)`.
- Batch fails if ≥5% rows invalid; otherwise continue and flag warnings.
- Return summary to uploader (processed, inserted, updated, failed counts).

### 7. Scheduled Sync
- Optional nightly job to re-import the latest Excel exports automatically.
- Maintain `import_settings` table storing SFTP/email source credentials if automation required.







