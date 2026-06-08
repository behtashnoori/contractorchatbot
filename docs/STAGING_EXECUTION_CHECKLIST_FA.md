# Checklist اجرای Staging پس از دریافت دسترسی

این checklist فقط بعد از آماده شدن دسترسی های staging اجرا می شود. تا قبل از دریافت staging server، DB staging، URLها، envها، migration access، مسیر upload و دسترسی backup/restore، هیچ deploy یا migration نباید انجام شود.

هیچ secret، password، token، API key یا connection string واقعی را در خروجی ترمینال عمومی، گزارش، Git یا chat ثبت نکنید.

## 1. دریافت اطلاعات Staging

- [ ] مسئول اجرای staging مشخص شده است.
- [ ] پنجره زمانی تست مشخص شده است.
- [ ] backend URL staging دریافت شده است.
- [ ] frontend URL staging دریافت شده است.
- [ ] KPI URL staging دریافت شده است.
- [ ] DB host/port/name staging دریافت شده است.
- [ ] روش deploy یا دسترسی SSH/RDP/CI مشخص شده است.
- [ ] مسیر logهای backend، frontend/proxy و KPI مشخص شده است.
- [ ] مسیر upload/import تست مشخص شده است.
- [ ] مسیر backup و policy نگهداری backup مشخص شده است.

## 2. تایید DB Staging و عدم اتصال به Production

- [ ] نام DB شامل staging یا شناسه غیر production است.
- [ ] host و network DB با production اشتباه گرفته نشده است.
- [ ] کاربر DB staging حداقل دسترسی لازم را دارد.
- [ ] `DATABASE_URL` بدون چاپ secret فقط از نظر host/name بررسی شده است.
- [ ] هیچ دستور migration تا قبل از این تایید اجرا نشده است.

## 3. ساخت Backup اولیه

- [ ] مسیر backup امن و قابل نوشتن است.
- [ ] backup قبل از migration گرفته شده است.
- [ ] نام فایل backup شامل تاریخ و محیط staging است.
- [ ] backup در log عمومی شامل password یا connection string نیست.
- [ ] owner نگهداری backup مشخص شده است.

نمونه دستور با placeholder:

```powershell
pg_dump -h <STAGING_DB_HOST> -p <STAGING_DB_PORT> -U <STAGING_DB_USER> -Fc -f <BACKUP_FILE> <STAGING_DB_NAME>
```

## 4. تنظیم Backend Env

- [ ] envهای backend از secret manager یا مسیر امن دریافت شده اند.
- [ ] `FLASK_ENV=staging` تنظیم شده است.
- [ ] `FLASK_DEBUG=0` تنظیم شده است.
- [ ] `SECRET_KEY` و `JWT_SECRET_KEY` مقدار واقعی، قوی و جدا دارند.
- [ ] `DATABASE_URL` فقط به DB staging اشاره می کند.
- [ ] `CORS_ALLOWED_ORIGINS` فقط frontend staging را مجاز می کند.
- [ ] `LOG_FORMAT=plain` یا مقدار معتبر تنظیم شده است.
- [ ] `MAX_CONTENT_LENGTH` با policy upload هماهنگ است.

## 5. اجرای Migration

- [ ] قبل از upgrade، revision فعلی با `flask db current` ثبت شده است.
- [ ] migration فقط روی DB staging اجرا می شود.
- [ ] `flask db upgrade` بدون خطا اجرا شده است.
- [ ] بعد از upgrade، revision نهایی با `flask db current` ثبت شده است.
- [ ] در صورت failure، سرویس بالا آورده نشده و علت ثبت شده است.

نمونه دستور با placeholder:

```powershell
cd backend
python -m flask db current
python -m flask db upgrade
python -m flask db current
```

## 6. اجرای Backend

- [ ] dependencyهای backend نصب شده اند.
- [ ] backend با env staging اجرا شده است.
- [ ] startup log بدون secret بررسی شده است.
- [ ] health یا endpoint پایه backend پاسخ می دهد.
- [ ] خطای CORS، DB connection یا JWT در startup دیده نمی شود.

## 7. Build و Deploy Frontend

- [ ] `VITE_API_BASE_URL=<STAGING_BACKEND_URL>` برای build تنظیم شده است.
- [ ] `npm.cmd run lint` یا lint معادل pass شده است.
- [ ] `npm.cmd run build` pass شده است.
- [ ] artifact frontend روی static server یا reverse proxy staging deploy شده است.
- [ ] frontend URL staging صفحه login را نمایش می دهد.

## 8. تنظیم CORS و Reverse Proxy

- [ ] TLS یا سیاست web server staging مشخص شده است.
- [ ] backend route از reverse proxy قابل دسترسی است.
- [ ] frontend route از reverse proxy قابل دسترسی است.
- [ ] KPI route یا service URL طبق طراحی قابل دسترسی است.
- [ ] CORS فقط frontend staging را allow می کند.
- [ ] origin نامعتبر header CORS دریافت نمی کند.
- [ ] rate limit برای `/auth/login` و `/auth/refresh` در proxy/WAF بررسی شده است.

## 9. اجرای KPI

- [ ] envهای KPI از مسیر امن تنظیم شده اند.
- [ ] KPI به DB staging وصل است، نه production.
- [ ] `GET /api/health` پاسخ سالم می دهد.
- [ ] درخواست بدون API key reject می شود.
- [ ] درخواست با API key staging پاسخ معتبر می دهد.
- [ ] export CSV/XLSX روی داده staging تست شده است.

## 10. Login Smoke

- [ ] login staff/admin با credential تست staging موفق است.
- [ ] `GET /auth/me` برای staff/admin پاسخ معتبر می دهد.
- [ ] login contractor تست staging موفق است.
- [ ] `GET /auth/me` برای contractor پاسخ scoped می دهد.
- [ ] credential demo یا production استفاده نشده است.

## 11. Invoice Smoke

- [ ] لیست invoice برای contractor فقط داده همان contractor را نشان می دهد.
- [ ] staff/admin می تواند داده مجاز سراسری را ببیند.
- [ ] invoice detail باز می شود.
- [ ] filter options پاسخ معتبر می دهد.
- [ ] responseها secret، password یا token برنمی گردانند.

## 12. Import Smoke

- [ ] upload `codtafsiltamin` با فایل کوچک تست موفق است.
- [ ] upload `contractors-1` با فایل کوچک تست موفق است.
- [ ] upload `contractors-2` با فایل کوچک تست موفق است.
- [ ] فایل invalid header با failure کنترل شده رد می شود.
- [ ] import ناموفق active data قبلی را خراب نمی کند.
- [ ] import دوم active batch switch را درست انجام می دهد.
- [ ] `ImportError` برای خطاهای کنترل شده قابل مشاهده است.

## 13. Rollback Smoke

- [ ] rollback به batch قبلی برای source تست شده انجام شده است.
- [ ] active records بعد از rollback درست هستند.
- [ ] contractor اجازه rollback ندارد و `403` می گیرد.
- [ ] target batch نامعتبر failure کنترل شده می دهد.
- [ ] audit log برای rollback موفق ثبت شده است.
- [ ] audit log برای rollback ناموفق ثبت شده است.

## 14. Backup/Restore Smoke

- [ ] restore drill روی DB جدا انجام شده است، نه روی production و نه روی DB فعال staging مگر با تایید رسمی.
- [ ] restore DB باز می شود.
- [ ] تعداد رکوردهای کلیدی با backup point مقایسه شده است.
- [ ] active batch state بعد از restore قابل بررسی است.
- [ ] فایل backup در storage امن نگهداری شده است.

نمونه دستور restore با placeholder:

```powershell
createdb <RESTORE_DB_NAME>
pg_restore -h <STAGING_DB_HOST> -p <STAGING_DB_PORT> -U <STAGING_DB_USER> -d <RESTORE_DB_NAME> <BACKUP_FILE>
```

## 15. ثبت نتیجه در گزارش

- [ ] نتیجه ها در `docs/STAGING_TEST_REPORT_TEMPLATE_FA.md` یا یک کپی تاریخ دار از آن ثبت شده اند.
- [ ] branch و commit تست شده ثبت شده است.
- [ ] revision migration قبل/بعد ثبت شده است.
- [ ] نتایج backend/frontend/KPI smoke ثبت شده است.
- [ ] defectها با owner و severity ثبت شده اند.
- [ ] تصمیم نهایی ثبت شده است: `PASS`، `PASS WITH RISK` یا `FAIL`.
- [ ] هیچ secret واقعی در گزارش ثبت نشده است.

## 16. معیار توقف فوری

در هرکدام از موارد زیر اجرای staging را متوقف کنید:

- احتمال اتصال به production DB وجود دارد.
- `DATABASE_URL`، token یا secret در log عمومی چاپ شده است.
- migration روی DB اشتباه شروع شده است.
- login/RBAC یا rollback access رفتار ناامن نشان می دهد.
- import داده active را بعد از failure خراب کرده است.
- backup قبل از migration وجود ندارد.
- restore drill یا راه rollback قابل تایید نیست.
