# Runbook بهره‌برداری و تحویل پروژه Contractor Chatbot

این سند برای نصب، اجرا، تست، migration، import، rollback، backup، restore و عیب‌یابی پروژه تهیه شده است. هیچ مقدار واقعی secret، password، token یا connection string در این سند نوشته نشده است.

## معرفی کوتاه سیستم

این پروژه یک وب‌اپ اطلاع‌رسانی وضعیت فاکتورها و صورتحساب‌های پیمانکاران است. پیمانکار پس از ورود فقط داده‌های مربوط به خودش را می‌بیند و کاربر staff/admin می‌تواند داده‌ها را مشاهده، فایل‌های Excel را import، وضعیت batchها را پیگیری و در صورت نیاز rollback کند.

کاربران اصلی:

- پیمانکار: مشاهده فاکتورها، وضعیت‌ها، مبالغ و جزئیات مربوط به خودش.
- staff/admin: مدیریت import، مشاهده داده‌های سراسری، ساخت user برای پیمانکار و عملیات rollback.
- مصرف‌کننده KPI: استفاده از microservice جداگانه `api/` برای گزارش‌های KPI و export.

اجزای اصلی:

- Backend اصلی: Flask، SQLAlchemy، Flask-Migrate، JWT و PostgreSQL.
- Frontend: React، Vite، MUI، React Router، TanStack Query و Axios.
- دیتابیس: PostgreSQL.
- KPI microservice: اپ Flask جداگانه در `api/` با API key مستقل.
- CI و امنیت: GitHub Actions برای backend tests، frontend lint/build و Gitleaks secret scanning.

## پیش‌نیازها

- Python 3.11 یا بالاتر. CI فعلی از Python 3.13 استفاده می‌کند.
- Node.js 22 برای همخوانی با CI. Node نسخه‌های جدیدتر LTS نیز معمولاً قابل استفاده‌اند.
- PostgreSQL 12 یا بالاتر. CI فعلی از PostgreSQL 16 استفاده می‌کند.
- Git.
- PowerShell روی Windows.
- دسترسی ساخت دیتابیس PostgreSQL برای محیط local/test.
- دسترسی تنظیم envهای production از طریق secret manager یا تنظیمات امن deploy.

## ساختار envها

فایل `.env` واقعی نباید commit شود. برای backend از `backend/config.example.env` به عنوان قالب استفاده کنید و مقدارهای واقعی را فقط در محیط local، CI secret یا secret manager نگه دارید.

### Backend

envهای مهم:

- `FLASK_APP`: معمولاً `wsgi.py`
- `FLASK_ENV`: `development`، `testing` یا مقدار مناسب محیط
- `FLASK_DEBUG`: فقط در local روشن باشد
- `FLASK_RUN_PORT`: پورت اجرای Flask، مانند `8000`
- `SECRET_KEY`: secret قوی برای Flask
- `JWT_SECRET_KEY`: secret قوی و جدا برای JWT
- `DATABASE_URL`: اتصال PostgreSQL با قالب `postgresql+psycopg://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:<DB_PORT>/<DB_NAME>`
- `CORS_ALLOWED_ORIGINS`: فهرست originهای مجاز، جداشده با comma
- `BCRYPT_LOG_ROUNDS`: هزینه hash رمز، مقدار نمونه امن در example برابر `12` است
- `MAX_CONTENT_LENGTH`: حداکثر حجم upload، پیش‌فرض example برابر 25MB است
- `LOG_LEVEL`: سطح log مثل `INFO`
- `LOG_FORMAT`: مقدار معتبر مثل `plain` یا percent-style معتبر؛ مقدار نامعتبر باید باعث crash نشود و fallback شود

### Frontend

- `VITE_API_BASE_URL`: آدرس backend، مثل `http://<API_HOST>:<API_PORT>`
- `VITE_API_TIMEOUT_MS`: timeout درخواست‌ها بر حسب میلی‌ثانیه، در صورت نیاز

### KPI/API

- `KPI_API_KEY`: کلید دسترسی به microservice KPI
- `PGHOST`
- `PGPORT`
- `PGUSER`
- `PGPASSWORD`
- `PGDATABASE`

## نصب و اجرای Backend

در PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item -Path .\config.example.env -Destination .\.env -Force
```

سپس `backend\.env` را ویرایش کنید و مقدارهای واقعی local را فقط همان‌جا قرار دهید. مقدار واقعی را در مستندات، خروجی ترمینال عمومی یا Git ننویسید.

اجرای migration:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m flask db upgrade
```

اجرای seed demo فقط برای local/test:

```powershell
python -m scripts.seed_demo_data
```

هشدار: credentialهای demo برای production مجاز نیستند. پس از اجرای seed در محیط غیرتستی، رمزها را rotate کنید یا از seed استفاده نکنید.

اجرای backend:

```powershell
python -m flask run --host=0.0.0.0
```

## نصب و اجرای Frontend

```powershell
cd frontend
npm install
npm run dev
```

برای build production:

```powershell
cd frontend
npm run build
```

برای preview build:

```powershell
cd frontend
npm run preview
```

## اجرای KPI Microservice

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r api\requirements.txt
$env:PGHOST="<DB_HOST>"
$env:PGPORT="<DB_PORT>"
$env:PGUSER="<DB_USER>"
$env:PGPASSWORD="<DB_PASSWORD>"
$env:PGDATABASE="<DB_NAME>"
$env:KPI_API_KEY="<KPI_API_KEY>"
$env:FLASK_APP="api/app.py"
.\.venv\Scripts\python -m flask run --port 5001
```

endpointهای اصلی KPI:

- `GET /api/health`
- `GET /api/kpi/yearly`
- `GET /api/kpi/yearly/export?format=csv|xlsx`
- `GET /kpi`

برای endpointهای KPI از `Authorization: Bearer <KPI_API_KEY>` یا `X-API-Key: <KPI_API_KEY>` استفاده کنید. کلید را در query string قرار ندهید.

## اجرای Migration

اجرای migration:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m flask db upgrade
```

بررسی revision فعلی:

```powershell
python -m flask db current
```

مشاهده history:

```powershell
python -m flask db history
```

نکات ایمنی قبل از migration production:

- از دیتابیس production backup بگیرید.
- مطمئن شوید `DATABASE_URL` به دیتابیس درست اشاره می‌کند.
- migration را ابتدا روی دیتابیس test/staging اجرا کنید.
- بعد از migration، backend tests و smoke test مسیرهای login، invoice و import را اجرا کنید.
- migration را روی دیتابیس اشتباه اجرا نکنید.

## تست‌ها

### Backend local

برای اجرای کامل integrationها باید `TEST_DATABASE_URL` به یک دیتابیس تست جدا اشاره کند و نام دیتابیس شامل `test` یا `pytest` باشد.

```powershell
cd backend
$env:TEST_DATABASE_URL="postgresql+psycopg://<TEST_USER>:<TEST_PASSWORD>@localhost:5432/<TEST_DB>"
$env:DATABASE_URL=$env:TEST_DATABASE_URL
$env:SECRET_KEY="pytest-secret-key-at-least-32-characters-long"
$env:JWT_SECRET_KEY="pytest-jwt-secret-key-at-least-32-chars-long"
$env:CORS_ALLOWED_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
python -m flask db upgrade
python -m pytest -rs
```

ساخت دیتابیس تست:

```powershell
createdb <TEST_DB>
```

یا در `psql`:

```sql
CREATE DATABASE <TEST_DB>;
CREATE USER <TEST_USER> WITH PASSWORD '<TEST_PASSWORD>';
GRANT ALL PRIVILEGES ON DATABASE <TEST_DB> TO <TEST_USER>;
```

اگر `TEST_DATABASE_URL` تنظیم نشود، تست‌های integration مربوط به auth، RBAC و invoice scope عمداً skip می‌شوند.

### Frontend

```powershell
cd frontend
npm.cmd run lint
npm.cmd run build
```

### CI

- `.github/workflows/ci.yml`: backend tests با PostgreSQL service، frontend lint و frontend build.
- `.github/workflows/security.yml`: secret scanning با Gitleaks.

در CI از `npm ci` استفاده می‌شود، چون `frontend/package-lock.json` وجود دارد.

## Import Operation

سه نوع import اصلی وجود دارد:

- `codtafsiltamin`: اطلاعات پیمانکار/تامین‌کننده را وارد `Contractor` می‌کند.
- `contractors-1`: خلاصه فاکتورها/روکش‌ها را وارد `InvoiceSummary` و در publish فعلی روی detailهای وابسته هم اثر فعال/غیرفعال دارد.
- `contractors-2`: جزئیات فاکتورها را وارد `InvoiceDetail` می‌کند و برای scope از summaryهای فعال کمک می‌گیرد.

endpointهای upload:

- `POST /admin/uploads/codtafsiltamin`
- `POST /admin/uploads/contractors-1`
- `POST /admin/uploads/contractors-2`

هر سه endpoint فقط برای staff/admin مجاز هستند و فایل را با field به نام `file` می‌پذیرند. مسیر عمومی `POST /admin/uploads` فقط batch placeholder می‌سازد و مسیر ingest اصلی نیست.

endpointهای وضعیت:

- `GET /admin/uploads/<batch_id>/progress`
- `GET /admin/uploads/<batch_id>`

active batch یعنی batch موفقی که رکوردهای آن با `is_active=True` در queryهای runtime دیده می‌شوند. import فعلی قبل از publish، preflight/validation انجام می‌دهد؛ اگر validation blocking شکست بخورد یا publish در transaction fail شود، داده فعال قبلی باید باقی بماند. batch زمانی active می‌شود که publish موفق شود، رکوردهای قدیمی inactive شوند، رکوردهای batch جدید active شوند، `published_at` ثبت شود و status به `done` برسد.

در صورت fail شدن import:

- batch با status شکست‌خورده علامت‌گذاری می‌شود.
- داده active قبلی نباید با import ناموفق جایگزین شود.
- خطاهای row/header در `ImportError` و وضعیت batch قابل بررسی هستند.
- error history طبق policy فعلی حذف خودکار نمی‌شود.

Retention policy فعلی:

- purge خودکار batch/error history وجود ندارد.
- آخرین batch موفق و batch فعال هر source نباید حذف شود.
- قبل از هر purge آینده باید dry-run، backup و policy تاییدشده وجود داشته باشد.

## Rollback Operation

endpoint rollback:

```text
POST /admin/imports/rollback
```

فقط staff/admin مجاز هستند.

ورودی مورد انتظار:

```json
{
  "source": "<codtafsiltamin|contractors-1|contractors-2>",
  "target_batch_id": "<BATCH_UUID>"
}
```

batch قابل rollback باید:

- وجود داشته باشد.
- `source` آن با درخواست یکی باشد.
- status آن `done` باشد.
- `published_at` داشته باشد.
- برای جدول‌های هدف حداقل یک رکورد مرتبط با `last_update_batch_id` همان batch داشته باشد.

batchهای ناموفق، publish نشده، بدون داده، یا مربوط به source دیگر قابل rollback نیستند.

در rollback:

- رکوردهای active فعلی source غیرفعال می‌شوند.
- رکوردهای batch هدف active می‌شوند.
- برای `codtafsiltamin`، userهای پیمانکار بر اساس `detail_code` به contractorهای batch هدف relink می‌شوند.
- rollback موفق و ناموفق در audit log ثبت می‌شود.
- پاسخ شامل source، target batch، batchهای فعال قبلی و تعداد رکوردهای فعال‌شده است.

نمونه request با placeholder:

```powershell
curl.exe -X POST "http://<API_HOST>:<API_PORT>/admin/imports/rollback" `
  -H "Authorization: Bearer <ACCESS_TOKEN>" `
  -H "Content-Type: application/json" `
  -d "{`"source`":`"<SOURCE>`",`"target_batch_id`":`"<BATCH_UUID>`"}"
```

## Backup و Restore

قبل از migration production یا import بزرگ backup بگیرید.

backup با `pg_dump`:

```powershell
pg_dump -h <DB_HOST> -p <DB_PORT> -U <DB_USER> -F c -f <BACKUP_FILE> <DB_NAME>
```

restore با `pg_restore` برای backup فرمت custom:

```powershell
pg_restore -h <DB_HOST> -p <DB_PORT> -U <DB_USER> -d <DB_NAME> --clean --if-exists <BACKUP_FILE>
```

restore با `psql` برای dump متنی:

```powershell
psql -h <DB_HOST> -p <DB_PORT> -U <DB_USER> -d <DB_NAME> -f <BACKUP_FILE>
```

هشدارهای عملیاتی:

- قبل از restore، نام دیتابیس مقصد را دوباره بررسی کنید.
- restore را روی دیتابیس production اشتباه اجرا نکنید.
- فایل backup را امن نگهداری کنید؛ ممکن است شامل داده حساس باشد.
- برای production، restore را ابتدا در staging تمرین کنید.

## سناریوهای اضطراری

| سناریو | علائم | بررسی | اقدام | ریسک |
|---|---|---|---|---|
| import با header نامعتبر | batch failed یا خطای validation | endpoint batch detail و `ImportError` | template درست را دانلود و فایل را اصلاح کنید؛ دوباره upload کنید | داده active قبلی باید باقی مانده باشد |
| import وسط publish شکست می‌خورد | status failed، error_id در log | log backend و batch detail | داده active قبلی را بررسی کنید؛ اگر ناقص شد از backup یا rollback استفاده کنید | اختلال نمایش داده |
| پیمانکار اطلاعات خودش را نمی‌بیند | dashboard خالی یا 403/404 | ارتباط `User.contractor_id`، active بودن `Contractor` و batch فعال | import codtafsiltamin و relink rollback را بررسی کنید | احتمال خطای mapping پیمانکار |
| پیمانکار اشتباهاً inactive شده | login هست ولی داده ندارد | رکوردهای active contractor و batch اخیر | rollback به batch سالم یا import اصلاح‌شده | اختلال دسترسی contractor |
| rollback لازم است | داده بعد از import جدید اشتباه است | batchهای `done` قبلی و source | `POST /admin/imports/rollback` با batch هدف | rollback اشتباه می‌تواند داده درست را جایگزین کند |
| migration fail می‌شود | خطای Alembic/DB | `flask db current`، backup، لاگ migration | اجرای migration را متوقف کنید، روی staging بازتولید کنید، در صورت نیاز restore | تغییر schema ناقص |
| frontend build fail می‌شود | `vite build` خطا می‌دهد | خروجی `npm run build` | dependencyها و lint را بررسی کنید؛ API contract را تغییر ندهید | deploy frontend متوقف می‌شود |
| backend test fail می‌شود | pytest failure | نام تست و fixture DB | اول failure امنیتی/RBAC را بررسی کنید؛ تست را بی‌دلیل ضعیف نکنید | regression امنیتی یا import |
| secret در repo پیدا می‌شود | Gitleaks fail | خروجی redacted scan | secret را rotate کنید؛ history rewrite فقط با تصمیم تیم | نشت credential |
| KPI service پاسخ نمی‌دهد | 500/timeout در KPI | envهای `PG*`، `KPI_API_KEY`، DB و log | service را با env درست restart کنید؛ health را تست کنید | گزارش KPI مختل می‌شود |

## Security Checklist

- فایل `.env` واقعی commit نشده باشد.
- secretها قوی باشند و در secret manager نگهداری شوند.
- secretهای demo یا local در production استفاده نشوند.
- `SECRET_KEY` و `JWT_SECRET_KEY` جدا و طولانی باشند.
- `CORS_ALLOWED_ORIGINS` در production فقط originهای واقعی را allow کند.
- Gitleaks در CI فعال و passing باشد.
- passwordهای demo بعد از هر seed غیرتستی rotate شوند.
- rollback فقط برای staff/admin فعال بماند.
- backupها امن نگهداری شوند.
- history scan برای repository production برنامه‌ریزی شود.

## Release Checklist

- backend tests با دیتابیس تست جدا pass شده‌اند.
- frontend lint pass شده است.
- frontend build pass شده است.
- secret scan pass شده است.
- migration روی test/staging اجرا شده است.
- backup production قبل از migration/import گرفته شده است.
- env production review شده و placeholder ندارد.
- CORS production دقیق تنظیم شده است.
- rollback plan و batch هدف احتمالی مشخص است.
- release tag ایجاد شده است.
- مسئول عملیات و زمان‌بندی deploy مشخص است.

