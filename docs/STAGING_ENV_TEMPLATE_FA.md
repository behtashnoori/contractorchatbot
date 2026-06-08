# Template محیط Staging

این سند template مقادیر env برای staging را مشخص می کند. همه مقدارها placeholder هستند. هیچ secret، password، token، API key یا connection string واقعی نباید در این فایل جایگزین یا commit شود.

## 1. Backend `.env.staging.example`

```text
FLASK_APP=<STAGING_FLASK_APP>
FLASK_ENV=staging
FLASK_DEBUG=0
FLASK_RUN_PORT=<STAGING_BACKEND_PORT>

SECRET_KEY=<STAGING_SECRET_KEY>
JWT_SECRET_KEY=<STAGING_JWT_SECRET_KEY>

DATABASE_URL=<STAGING_DATABASE_URL>
CORS_ALLOWED_ORIGINS=<STAGING_FRONTEND_ORIGIN>

JWT_ACCESS_TOKEN_EXPIRES=<ACCESS_TOKEN_SECONDS>
JWT_REFRESH_TOKEN_EXPIRES=<REFRESH_TOKEN_SECONDS>

BCRYPT_LOG_ROUNDS=12
MAX_CONTENT_LENGTH=<MAX_UPLOAD_BYTES>

LOG_LEVEL=INFO
LOG_FORMAT=plain

KPI_API_KEY=<STAGING_KPI_API_KEY>
```

چک های backend:

- `FLASK_ENV` باید `staging` باشد.
- `FLASK_DEBUG` باید `0` باشد.
- `SECRET_KEY` و `JWT_SECRET_KEY` باید قوی، جدا و حداقل 32 کاراکتر باشند.
- `DATABASE_URL` باید فقط به DB staging اشاره کند.
- `CORS_ALLOWED_ORIGINS` باید فقط origin frontend staging را داشته باشد.
- local origins، wildcard و production URL نباید بدون تایید رسمی در staging استفاده شوند.

## 2. Frontend `.env.staging.example`

```text
VITE_API_BASE_URL=<STAGING_BACKEND_URL>
VITE_API_TIMEOUT_MS=<TIMEOUT_MS>
```

چک های frontend:

- build staging باید با backend URL staging ساخته شود.
- مقدار `VITE_API_BASE_URL` نباید local یا production باشد.
- پس از build، smoke test login و dashboard باید از frontend URL staging انجام شود.

## 3. KPI `.env.staging.example`

```text
KPI_API_KEY=<STAGING_KPI_API_KEY>
PGHOST=<STAGING_DB_HOST>
PGPORT=<STAGING_DB_PORT>
PGUSER=<STAGING_DB_USER>
PGPASSWORD=<STAGING_DB_PASSWORD>
PGDATABASE=<STAGING_DB_NAME>
```

چک های KPI:

- `KPI_API_KEY` باید جدا از production و خارج از Git نگهداری شود.
- `PG*` باید به DB staging اشاره کند.
- KPI باید با `GET /api/health` تست شود.
- درخواست بدون API key باید reject شود.
- API key نباید در query string ارسال شود.

## 4. مقادیر ممنوع در template

موارد زیر نباید در این فایل یا هیچ سند عمومی دیگری نوشته شوند:

- password واقعی DB
- connection string واقعی
- مقدار واقعی `SECRET_KEY`
- مقدار واقعی `JWT_SECRET_KEY`
- مقدار واقعی `KPI_API_KEY`
- token تست یا production
- URL یا credential production

## 5. روش تحویل مقدارهای واقعی

مقدارهای واقعی باید فقط از یکی از روش های امن زیر تحویل شوند:

- secret manager سازمان
- CI/CD protected variables
- کانال امن مورد تایید تیم زیرساخت
- فایل `.env` روی سرور staging با دسترسی محدود و خارج از Git

اگر مقدارها از طریق ticket ثبت می شوند، باید redacted باشند و فقط owner و مسیر امن تحویل مشخص شود.
