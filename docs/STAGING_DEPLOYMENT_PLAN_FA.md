# برنامه اجرای Staging برای Contractor Portal

این سند برنامه عملیاتی اجرای staging است. در این فاز deployment واقعی انجام نشده است، چون دسترسی صریح و امن به سرور staging در workspace وجود ندارد. هیچ secret، password، token، connection string واقعی یا فایل `.env` واقعی نباید در این سند، لاگ، Git یا خروجی عمومی ثبت شود.

## 1. هدف Staging

- اجرای واقعی migration روی دیتابیس staging جدا از production.
- تست backend و frontend در محیط نزدیک به production.
- تست import و rollback با فایل‌های کوچک و کنترل‌شده.
- تست login پیمانکار و staff/admin.
- تست KPI microservice و exportهای آن.
- تست backup/restore قبل از هر تغییر پرریسک.
- تست CORS، envها، audit و رفتار tokenها در محیط staging.

## 2. اجزای Staging

- Backend Flask: سرویس اصلی API با PostgreSQL و JWT.
- Frontend React build: خروجی `npm run build` و سرو شدن static assets.
- PostgreSQL staging DB: دیتابیس مستقل، غیر production، با backup اولیه.
- KPI microservice: سرویس جدا در پوشه `api/` با API key جدا.
- Reverse proxy: در صورت وجود، برای TLS، routing، rate limit و headerهای امنیتی.
- Env staging: فقط در secret manager یا فایل خارج از Git.
- Log paths: مسیر جدا برای backend، reverse proxy، frontend/static server و KPI.

## 3. Envهای Staging

Backend:

```text
FLASK_APP=<STAGING_FLASK_APP>
FLASK_ENV=staging
FLASK_DEBUG=0
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
```

Frontend:

```text
VITE_API_BASE_URL=<STAGING_BACKEND_URL>
VITE_API_TIMEOUT_MS=<TIMEOUT_MS>
```

KPI:

```text
KPI_API_KEY=<STAGING_KPI_API_KEY>
PGHOST=<STAGING_DB_HOST>
PGPORT=<STAGING_DB_PORT>
PGUSER=<STAGING_DB_USER>
PGPASSWORD=<STAGING_DB_PASSWORD>
PGDATABASE=<STAGING_DB_NAME>
```

قواعد امنیتی env:

- `DATABASE_URL` staging نباید به production اشاره کند.
- نام دیتابیس staging باید واضح باشد، مثل `<APP>_staging`.
- `SECRET_KEY`, `JWT_SECRET_KEY` و `KPI_API_KEY` باید جدا و تصادفی باشند.
- `CORS_ALLOWED_ORIGINS` فقط origin واقعی frontend staging را داشته باشد.
- originهای local و wildcard در staging واقعی مجاز نیستند مگر برای تست محدود و ثبت‌شده.

## 4. مراحل اجرای Staging

1. پنجره اجرای staging، مسئول اجرا و مسئول تایید را مشخص کنید.
2. اگر staging از copy داده فعلی ساخته می‌شود، از source DB backup بگیرید.
3. دیتابیس staging را بسازید و نام آن را دوباره بررسی کنید که production نباشد.
4. user/role دیتابیس staging را با حداقل دسترسی لازم ایجاد کنید.
5. envهای backend را در secret manager یا کانال امن deploy تنظیم کنید.
6. وابستگی‌های backend را نصب کنید: `pip install -r requirements.txt`.
7. قبل از migration، روی staging اجرا کنید: `python -m flask db current`.
8. migration را اجرا کنید: `python -m flask db upgrade`.
9. revision نهایی را بررسی کنید: `python -m flask db current`.
10. backend را با env staging اجرا کنید.
11. health و خطاهای startup backend را بررسی کنید.
12. frontend را با `VITE_API_BASE_URL=<STAGING_BACKEND_URL>` build کنید.
13. خروجی frontend build را روی static server یا reverse proxy staging deploy کنید.
14. CORS و reverse proxy را با origin staging تنظیم کنید.
15. KPI service را با envهای `PG*` و `KPI_API_KEY` staging اجرا کنید.
16. health checkهای backend، frontend و KPI را اجرا کنید.
17. login smoke test پیمانکار و staff/admin را انجام دهید.
18. import smoke test برای هر سه فایل انجام دهید.
19. rollback smoke test به batch موفق قبلی را اجرا کنید.
20. backup/restore smoke test را روی دیتابیس staging یا restore DB جدا اجرا کنید.
21. نتایج را در `STAGING_TEST_REPORT_TEMPLATE_FA.md` ثبت کنید.
22. تصمیم sign-off را ثبت کنید: pass، pass with risk، یا fail.

## 5. Migration Validation

دستورهای نمونه:

```powershell
cd backend
$env:DATABASE_URL="<STAGING_DATABASE_URL>"
$env:SECRET_KEY="<STAGING_SECRET_KEY>"
$env:JWT_SECRET_KEY="<STAGING_JWT_SECRET_KEY>"
$env:CORS_ALLOWED_ORIGINS="<STAGING_FRONTEND_ORIGIN>"
python -m flask db current
python -m flask db upgrade
python -m flask db current
```

چک‌ها:

- قبل از اجرای migration، مقدار `DATABASE_URL` را بدون چاپ secret با نام دیتابیس و host تایید کنید.
- migration نباید روی production DB اجرا شود.
- revision بعد از upgrade باید با آخرین migration repo برابر باشد.
- جدول‌ها و ستون‌های active batch مانند `is_active`, `last_update_batch_id`, `published_at`, `replaced_by_batch_id` بررسی شوند.
- اگر migration شکست خورد، سرویس را بالا نیاورید؛ علت را ثبت کنید و فقط روی staging بازتولید کنید.

## 6. Smoke Tests

Backend:

- [ ] `POST /auth/login` با staff/admin staging.
- [ ] `POST /auth/login` با contractor staging.
- [ ] `GET /auth/me` با access token معتبر.
- [ ] `GET /invoices/` برای contractor و staff/admin.
- [ ] `GET /invoices/filters/options`.
- [ ] `POST /admin/uploads` با contractor باید `403` بدهد.
- [ ] `POST /admin/uploads` با staff/admin بدون فایل باید validation امن بدهد.
- [ ] `POST /admin/imports/rollback` با contractor باید `403` بدهد.

Frontend:

- [ ] صفحه login باز می‌شود.
- [ ] login پیمانکار به dashboard می‌رسد.
- [ ] dashboard فاکتورها load می‌شود.
- [ ] invoice detail باز می‌شود.
- [ ] login staff/admin به admin upload page دسترسی دارد.
- [ ] contractor به admin upload page دسترسی ندارد.

Import:

- [ ] `codtafsiltamin` با فایل کوچک موفق import می‌شود.
- [ ] `contractors-1` با فایل summary کوچک موفق import می‌شود.
- [ ] `contractors-2` با فایل detail کوچک موفق import می‌شود.
- [ ] فایل خراب با header غلط fail کنترل‌شده می‌دهد و active data قبلی را خراب نمی‌کند.
- [ ] import دوم active batch را عوض می‌کند و batch قبلی قابل rollback می‌ماند.

Rollback:

- [ ] rollback به batch اول انجام می‌شود.
- [ ] active records بعد از rollback درست هستند.
- [ ] userهای contractor در rollback `codtafsiltamin` درست relink می‌شوند.
- [ ] audit log برای rollback موفق ثبت شده است.
- [ ] rollback نامعتبر audit failure ثبت می‌کند.

Security:

- [ ] CORS فقط origin staging را allow می‌کند.
- [ ] origin غیرمجاز header CORS نمی‌گیرد.
- [ ] contractor به endpointهای admin دسترسی ندارد.
- [ ] rollback فقط staff/admin است.
- [ ] token کاربر حذف‌شده یا contractor inactive رد می‌شود.
- [ ] responseها secret، password یا token برنمی‌گردانند.

KPI:

- [ ] `GET /api/health` پاسخ سالم می‌دهد.
- [ ] request بدون API key معتبر رد می‌شود.
- [ ] `GET /api/kpi/yearly` با API key staging پاسخ می‌دهد.
- [ ] export CSV/XLSX با داده staging تست می‌شود.

## 7. Data Test Plan

فایل‌های نمونه باید کوچک، ساختگی و غیر production باشند:

- فایل پیمانکار با 2 پیمانکار:
  - یک contractor فعال برای login.
  - یک contractor دیگر برای تست scope.
- فایل summary با 2 روکش:
  - یک روکش برای contractor اول.
  - یک روکش برای contractor دوم.
- فایل detail با چند ردیف:
  - حداقل دو detail برای یک روکش.
  - یک detail برای روکش دوم.
- فایل خراب:
  - header الزامی حذف یا اشتباه شود تا validation fail کنترل‌شده تست شود.
- import دوم:
  - مقدار status یا مبلغ را تغییر دهد تا active batch switch قابل مشاهده باشد.
- rollback:
  - rollback به batch اول و بررسی برگشت داده‌ها.

داده تست نباید شامل اطلاعات واقعی پیمانکار، password واقعی، شماره حساب واقعی یا داده production باشد.

## 8. Backup/Restore Staging

Backup نمونه:

```powershell
pg_dump -h <DB_HOST> -p <DB_PORT> -U <DB_USER> -Fc -f <BACKUP_FILE> <DB_NAME>
```

Restore نمونه:

```powershell
createdb <RESTORE_DB_NAME>
pg_restore -h <DB_HOST> -p <DB_PORT> -U <DB_USER> -d <RESTORE_DB_NAME> <BACKUP_FILE>
```

چک‌ها:

- restore را روی دیتابیس جدا انجام دهید، نه روی دیتابیس staging فعال مگر در drill کنترل‌شده.
- فایل backup را encrypted یا در storage محدود نگهداری کنید.
- پس از restore، تعداد رکوردهای کلیدی و آخرین batchهای فعال را مقایسه کنید.

## 9. Rollback Plan

Rollback داده import:

- از `POST /admin/imports/rollback` با `source` و `target_batch_id` استفاده کنید.
- فقط batchهای `done` و `published_at`دار هدف rollback باشند.
- بعد از rollback، active records و audit log را بررسی کنید.

Rollback migration:

- تا وقتی backup/restore تست نشده، downgrade روی staging فعال انجام ندهید.
- اگر migration schema-breaking بود، برنامه اصلی rollback باید restore backup باشد.
- دستورهای Alembic downgrade فقط پس از review دستی migration و تست روی restore DB اجرا شوند.

Rollback release:

- backend artifact یا branch قبلی را مشخص کنید.
- frontend build قبلی را نگه دارید.
- env را تغییر ندهید مگر علت failure env باشد.
- پس از rollback release، smoke tests login/invoices/admin را دوباره اجرا کنید.

زمان rollback:

- failure در migration.
- failure در login یا RBAC.
- خراب شدن active data پس از import.
- failure در rollback smoke.
- خطای امنیتی مانند CORS باز یا دسترسی contractor به admin.

## 10. Sign-Off Checklist

- [ ] backend healthy است.
- [ ] frontend healthy است.
- [ ] migration OK است.
- [ ] import هر سه فایل OK است.
- [ ] rollback OK است.
- [ ] backup/restore OK است.
- [ ] security smoke OK است.
- [ ] KPI OK است.
- [ ] CI/security branch سبز است یا نتیجه remote run ثبت شده است.
- [ ] ریسک‌های شناخته‌شده پذیرفته یا blocker شده‌اند.
- [ ] تصمیم نهایی ثبت شده است: pass، pass with risk، یا fail.

## 11. ریسک‌های باقی‌مانده قبل از Production

- rate limiting داخلی login هنوز runtime نشده است.
- refresh token هنوز در `localStorage` نگهداری می‌شود.
- password پیمانکار تا بازطراحی password/reset flow قابل حدس است.
- history scan کامل باید در محیط امن اجرا شود.
- staging واقعی باید قبل از production با همین checklist اجرا و sign-off شود.
