# درخواست آماده سازی محیط Staging

مخاطب: تیم زیرساخت / ادمین سرور

این سند برای آماده سازی محیط staging سامانه اطلاع رسانی فاکتور پیمانکاران تهیه شده است. هدف، فراهم کردن یک محیط جدا از production است تا تیم پروژه بتواند migration، smoke test، import، rollback، KPI و بررسی های امنیتی را بدون خطر برای داده و سرویس production انجام دهد.

هیچ secret، password، token، API key یا connection string واقعی نباید در این سند، Git، chat یا ticket عمومی نوشته شود. مقادیر واقعی فقط باید از طریق secret manager یا کانال امن مورد تایید سازمان تحویل شوند.

## 1. هدف درخواست

برای اجرای تست staging سامانه اطلاع رسانی فاکتور پیمانکاران، به یک محیط staging مستقل از production نیاز داریم. این محیط باید امکان اجرای backend Flask، frontend React build، microservice KPI، PostgreSQL staging، migration کنترل شده، upload فایل تست، backup و restore drill را فراهم کند.

خروجی مورد انتظار از تیم زیرساخت این است که endpointها، دسترسی ها، مسیرها و سیاست های لازم را بدون افشای secret آماده و در جدول تحویل همین سند ثبت کند.

## 2. اقلام مورد نیاز

1. سرور یا VM staging جدا از production.
2. روش deploy مشخص، مانند SSH/RDP، CI deploy یا دسترسی کنترل شده عملیاتی.
3. PostgreSQL staging database جدا از production.
4. backend staging URL.
5. frontend staging URL.
6. KPI service URL.
7. reverse proxy یا web server برای routing، TLS و headerهای امنیتی.
8. مسیر logها برای backend، frontend/static server یا proxy، و KPI.
9. مسیر backup امن و محدود.
10. دسترسی اجرای migration روی DB staging.
11. دسترسی اجرای backup/restore یا restore drill روی DB جدا.
12. storage موقت برای فایل های upload/import تستی.
13. دسترسی محدود برای تست کننده ها، جدا از دسترسی production.
14. policy نگهداری backup، شامل مدت نگهداری، encryption و owner.

## 3. مشخصات پیشنهادی Staging

این موارد پیشنهادی/قابل تنظیم هستند و تیم زیرساخت می تواند بر اساس استاندارد سازمان آنها را نهایی کند.

| مورد | پیشنهاد حداقلی |
| --- | --- |
| CPU | 2 vCPU پیشنهادی/قابل تنظیم |
| RAM | 4 GB پیشنهادی/قابل تنظیم |
| Disk app/log | 30 GB پیشنهادی/قابل تنظیم |
| Disk DB | 30 GB یا بیشتر، متناسب با داده تست |
| OS | Linux Server LTS پیشنهادی/قابل تنظیم |
| PostgreSQL | 12 یا بالاتر؛ ترجیحا هم نسخه با production یا CI |
| Python | 3.11 یا بالاتر؛ CI فعلی با Python 3.13 نیز سازگار است |
| Node.js | 22 برای همخوانی با CI/frontend build |
| فضای backup | حداقل 2 نسخه backup staging یا مطابق policy سازمان |
| پورت backend | 8000 داخلی یا مقدار استاندارد سازمان |
| پورت frontend/static | 80/443 از طریق reverse proxy |
| پورت KPI | 5001 داخلی یا پشت reverse proxy |
| پورت PostgreSQL | 5432 فقط از شبکه مجاز |

## 4. شبکه و آدرس ها

لطفا مقدارهای واقعی را فقط در کانال امن تحویل دهید. در ticket عمومی می توان از شناسه یا آدرس redacted استفاده کرد.

```text
<STAGING_BACKEND_URL>
<STAGING_FRONTEND_URL>
<STAGING_KPI_URL>
<STAGING_DB_HOST>
<STAGING_DB_PORT>
```

الزامات شبکه:

- backend، frontend و KPI باید به محیط staging اشاره کنند، نه production.
- `CORS_ALLOWED_ORIGINS` فقط origin frontend staging را مجاز کند.
- DB staging از production جدا باشد و نام آن به وضوح staging بودن را نشان دهد.
- دسترسی مستقیم DB فقط برای سرویس های لازم، migration runner و ادمین مجاز باشد.
- rate limit برای مسیرهای login و refresh در reverse proxy یا WAF پیشنهاد می شود.

## 5. Envهای مورد نیاز Backend

نمونه زیر فقط placeholder است و نباید به عنوان فایل `.env` واقعی commit شود.

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
KPI_API_KEY=<STAGING_KPI_API_KEY>
```

## 6. Envهای مورد نیاز Frontend

```text
VITE_API_BASE_URL=<STAGING_BACKEND_URL>
VITE_API_TIMEOUT_MS=<TIMEOUT_MS>
```

Frontend باید با مقدار staging ساخته شود و هیچ URL مربوط به local یا production در artifact staging باقی نماند.

## 7. Envهای مورد نیاز KPI

```text
KPI_API_KEY=<STAGING_KPI_API_KEY>
PGHOST=<STAGING_DB_HOST>
PGPORT=<STAGING_DB_PORT>
PGUSER=<STAGING_DB_USER>
PGPASSWORD=<STAGING_DB_PASSWORD>
PGDATABASE=<STAGING_DB_NAME>
```

KPI API key نباید در query string استفاده شود. برای فراخوانی KPI از header امن مانند `Authorization: Bearer <KPI_API_KEY>` یا `X-API-Key: <KPI_API_KEY>` استفاده شود.

## 8. الزامات امنیتی

- staging باید از production جدا باشد.
- secretها در Git، chat، log عمومی یا فایل مستندات ذخیره نشوند.
- فایل `.env` واقعی فقط روی سرور یا secret manager نگهداری شود.
- CORS فقط frontend staging را مجاز کند.
- DB staging از production جدا باشد و نام آن شامل staging باشد.
- اگر از copy production استفاده می شود، داده حساس باید طبق تصمیم سازمانی کنترل، anonymize یا محدود شود.
- قبل از migration، backup staging گرفته شود.
- دسترسی rollback فقط برای staff/admin باشد.
- credentialهای demo یا local نباید در staging واقعی فعال بمانند مگر برای تست محدود و با تصمیم ثبت شده.
- backupها encrypted یا در storage محدود نگهداری شوند.
- مسیرهای log نباید password، token، connection string یا payload حساس ثبت کنند.

## 9. تحویل مورد انتظار از تیم زیرساخت

| مورد | مقدار/آدرس | مسئول | وضعیت | توضیح |
| --- | --- | --- | --- | --- |
| Staging server/VM | `<SERVER_ID_OR_HOST>` | `<OWNER>` | `<TODO/DONE>` | `<NOTES>` |
| روش deploy | `<SSH_RDP_CI_OR_OTHER>` | `<OWNER>` | `<TODO/DONE>` | `<NOTES>` |
| Backend URL | `<STAGING_BACKEND_URL>` | `<OWNER>` | `<TODO/DONE>` | `<NOTES>` |
| Frontend URL | `<STAGING_FRONTEND_URL>` | `<OWNER>` | `<TODO/DONE>` | `<NOTES>` |
| KPI URL | `<STAGING_KPI_URL>` | `<OWNER>` | `<TODO/DONE>` | `<NOTES>` |
| DB host/port | `<STAGING_DB_HOST>:<STAGING_DB_PORT>` | `<OWNER>` | `<TODO/DONE>` | secretها جدا تحویل شوند |
| DB name | `<STAGING_DB_NAME>` | `<OWNER>` | `<TODO/DONE>` | نباید production باشد |
| Migration access | `<YES_NO_AND_METHOD>` | `<OWNER>` | `<TODO/DONE>` | دسترسی محدود |
| Backup path | `<BACKUP_SAFE_LOCATION>` | `<OWNER>` | `<TODO/DONE>` | بدون secret |
| Restore drill access | `<YES_NO_AND_METHOD>` | `<OWNER>` | `<TODO/DONE>` | روی DB جدا |
| Upload/import storage | `<STAGING_UPLOAD_PATH>` | `<OWNER>` | `<TODO/DONE>` | برای فایل های تست |
| Backend log path | `<BACKEND_LOG_PATH>` | `<OWNER>` | `<TODO/DONE>` | دسترسی read برای QA |
| Frontend/proxy log path | `<FRONTEND_OR_PROXY_LOG_PATH>` | `<OWNER>` | `<TODO/DONE>` | دسترسی read برای QA |
| KPI log path | `<KPI_LOG_PATH>` | `<OWNER>` | `<TODO/DONE>` | دسترسی read برای QA |
| Reverse proxy config owner | `<OWNER>` | `<OWNER>` | `<TODO/DONE>` | TLS/CORS/rate limit |
| Backup retention policy | `<RETENTION_POLICY>` | `<OWNER>` | `<TODO/DONE>` | مدت نگهداری و encryption |

## 10. معیار آماده بودن برای اجرای تست Staging

محیط زمانی آماده تست است که همه موارد زیر تایید شده باشند:

- backend، frontend و KPI URLهای staging قابل دسترس باشند.
- DB staging جدا از production باشد.
- envهای staging بدون افشای secret تنظیم شده باشند.
- migration runner بتواند فقط به DB staging وصل شود.
- backup قبل از migration قابل اجرا باشد.
- upload/import storage آماده و قابل نوشتن باشد.
- logهای runtime قابل مشاهده باشند.
- CORS و reverse proxy فقط originهای مجاز staging را allow کنند.
- تیم پروژه بتواند checklist اجرای staging را از `docs/STAGING_EXECUTION_CHECKLIST_FA.md` شروع کند.
