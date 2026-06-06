# خلاصه تثبیت و وضعیت تحویل پروژه

این سند خلاصه مدیریتی/فنی وضعیت پروژه پس از فازهای تثبیت backend، import، frontend، امنیت و CI است. مقدار واقعی هیچ secret یا credential در این سند درج نشده است.

## وضعیت قبل از تثبیت

- بخشی از تست‌های backend به دلیل نبود `TEST_DATABASE_URL` skip می‌شدند.
- `LOG_FORMAT` نامعتبر، از جمله مقدار `json`، می‌توانست startup یا pytest را دچار مشکل کند.
- importer پیمانکار با مدل `Contractor` ناسازگاری داشت.
- importهای Excel پیش از تثبیت، ریسک حذف یا commit داده قبلی پیش از موفقیت کامل import جدید داشتند.
- RBAC نسبت به stale role در token/request context نیازمند اصلاح بود.
- frontend lint fail می‌شد و logهای غیرضروری/حساس در console وجود داشت.
- docs/scripts/config sampleها دارای credentialهای واقعی‌نما یا fallbackهای نامناسب بودند.
- secret scanning و CI کامل هنوز آماده نبودند.

## کارهای انجام‌شده

- اصلاح سازگاری `CodTafsiltaminImporter` با مدل `Contractor`.
- مقاوم‌سازی logging در برابر `LOG_FORMAT` خالی یا نامعتبر.
- آماده‌سازی و مستندسازی `TEST_DATABASE_URL` با guard نام دیتابیس test/pytest.
- اجرای واقعی تست‌های integration auth، RBAC و invoice scope روی دیتابیس تست جدا.
- اصلاح RBAC تا تصمیم staff/admin بر اساس role تازه کاربر در دیتابیس انجام شود.
- افزودن preflight و publish transaction-safe برای importها.
- افزودن active batch/versioning برای `Contractor`، `InvoiceSummary` و `InvoiceDetail`.
- افزودن rollback API برای importها.
- افزودن audit log برای عملیات مهم login/import/rollback.
- افزودن retention policy برای batch و error history.
- cleanup frontend: lint pass، حذف/محدودسازی console logهای غیرضروری و helper مشترک status.
- cleanup secret hygiene در docs/scripts/config sampleها و تکمیل `.gitignore`.
- افزودن `.gitleaks.toml` و `.github/workflows/security.yml`.
- افزودن `.github/workflows/ci.yml` برای backend tests، frontend lint و frontend build.
- تهیه مستندات فنی import و تست دیتابیس.

## وضعیت فعلی Backend

- Backend اصلی با Flask، SQLAlchemy، Flask-Migrate، JWT، bcrypt و PostgreSQL کار می‌کند.
- migrationها شامل جدول‌های اولیه، progress import، role کاربر، audit log و active batch versioning هستند.
- تست‌های backend در آخرین اجرای محلی با دیتابیس تست جدا pass شده‌اند:

```text
34 passed
0 failed
0 skipped
```

- endpointهای admin با guard staff/admin محافظت می‌شوند.
- role برای authorization از وضعیت تازه user در دیتابیس enforce می‌شود.

## وضعیت فعلی Frontend

- Frontend با React/Vite/MUI ساخته شده است.
- مسیرهای اصلی شامل landing، login، dashboard فاکتورها، جزئیات invoice و admin upload هستند.
- lint و build در آخرین اجرای محلی pass شده‌اند.
- status rendering یکدست‌تر شده و console logهای غیرضروری/حساس production حذف یا محدود شده‌اند.

## وضعیت Import و Rollback

- importهای `codtafsiltamin`، `contractors-1` و `contractors-2` preflight دارند.
- publish داده‌های preflight شده در transaction انجام می‌شود.
- رکوردهای جدید با `last_update_batch_id` و `is_active=True` منتشر می‌شوند.
- داده‌های active قبلی به جای حذف فیزیکی، inactive می‌شوند.
- batch موفق `published_at` دارد و برای rollback قابل استفاده است.
- rollback از طریق `POST /admin/imports/rollback` انجام می‌شود و فقط staff/admin مجاز هستند.
- rollback `codtafsiltamin` userهای پیمانکار را بر اساس `detail_code` به contractorهای batch هدف relink می‌کند.
- batch/error history فعلاً purge خودکار ندارد تا امکان audit و rollback حفظ شود.

## وضعیت CI و Secret Hygiene

- workflow امنیتی جدا برای Gitleaks وجود دارد:

```text
.github/workflows/security.yml
```

- workflow CI کامل وجود دارد:

```text
.github/workflows/ci.yml
```

- backend job در CI از PostgreSQL service با دیتابیس تستی `contractor_portal_pytest` استفاده می‌کند.
- frontend job با `npm ci`، lint و build اجرا می‌شود.
- فایل‌های env واقعی همچنان نباید commit شوند.
- اگر secret واقعی در history قدیمی وجود داشته باشد، این فاز history rewrite انجام نداده است؛ باید secret rotate و history scan با تصمیم تیم انجام شود.

## ریسک‌های باقی‌مانده

| ریسک | شدت | توضیح | پیشنهاد |
|---|---:|---|---|
| history scan کامل انجام نشده | متوسط/زیاد | working tree clean کافی نیست اگر secret قبلاً commit شده باشد | اجرای Gitleaks history scan در محیط امن و rotate هر secret واقعی |
| deploy/runbook production هنوز عملیاتی نشده | متوسط | Docker/service unit/monitoring رسمی در repo تثبیت نشده است | طراحی deployment target و smoke test production |
| تولید password پیمانکار | متوسط/زیاد | اگر password قابل حدس یا demo در production استفاده شود ریسک امنیتی دارد | password تصادفی، reset اجباری و کانال تحویل امن |
| refresh token در localStorage | متوسط | در XSS قابل سرقت است | بررسی HttpOnly cookie، CSP و token rotation |
| purge history پیاده‌سازی نشده | کم/متوسط | فعلاً برای rollback خوب است، ولی در بلندمدت حجم داده زیاد می‌شود | طراحی purge dry-run با retention policy تاییدشده |
| KPI microservice جدا از backend اصلی | متوسط | auth/observability/deploy مستقل دارد | مستندسازی deployment و health monitoring جدا |
| CI فقط پس از push در GitHub تایید نهایی می‌شود | کم/متوسط | validation محلی انجام شده ولی GitHub runner ممکن است تفاوت محیطی داشته باشد | اجرای اولین workflow و اصلاح issues محیطی احتمالی |

## پیشنهاد فاز بعدی

1. اجرای GitHub Actions روی branch واقعی و ثبت نتیجه CI/security.
2. تهیه deployment plan برای محیط staging/production شامل process manager، reverse proxy، TLS و health check.
3. اجرای history scan امن و تصمیم درباره rotate/history rewrite در صورت کشف secret.
4. تکمیل سیاست password پیمانکار و reset/change-password امن برای production.
5. افزودن monitoring، structured logging و alert برای import/rollback/failure.
6. طراحی purge-history command با dry-run و backup prerequisite.

## وضعیت تحویل

پروژه برای ورود به فاز آماده‌سازی بهره‌برداری/staging آماده‌تر شده است: backend و frontend gateهای اصلی را پاس می‌کنند، import و rollback کنترل‌شده‌تر هستند، secret hygiene و CI اضافه شده‌اند و runbook عملیاتی برای ادامه کار وجود دارد. قبل از production واقعی همچنان باید deployment، monitoring، secret rotation و سیاست password پیمانکار نهایی شود.

