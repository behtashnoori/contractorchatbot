# چک‌لیست آمادگی Release و تحویل پروژه

این سند برای آخرین بررسی پیش از push/PR، اجرای GitHub Actions، ورود به staging و آماده‌سازی production تهیه شده است. این فاز قابلیت جدید، migration جدید یا endpoint جدید اضافه نمی‌کند.

## وضعیت فعلی

### Backend

- backend با Flask، SQLAlchemy، Flask-Migrate، JWT، bcrypt و PostgreSQL تثبیت شده است.
- تست‌های backend در اجرای محلی با دیتابیس تست جدا pass شده‌اند.
- RBAC و scope پیمانکار با تست‌های integration پوشش داده شده‌اند.
- guard دیتابیس تست اجازه اجرای integration روی دیتابیس غیرتستی را نمی‌دهد.

### Frontend

- frontend با React/Vite/MUI کار می‌کند.
- lint و build محلی pass شده‌اند.
- cleanup مربوط به console logهای غیرضروری و status rendering انجام شده است.

### Import و Rollback

- importهای `codtafsiltamin`، `contractors-1` و `contractors-2` preflight دارند.
- publish داده‌ها transaction-safeتر شده و رکوردهای فعال با `is_active` و `last_update_batch_id` کنترل می‌شوند.
- rollback از طریق `POST /admin/imports/rollback` برای staff/admin وجود دارد.
- purge خودکار batch/error history فعلاً وجود ندارد تا audit و rollback حفظ شود.

### CI

- `.github/workflows/ci.yml` شامل backend tests با PostgreSQL service، frontend lint و frontend build است.
- `.github/workflows/security.yml` شامل Gitleaks secret scanning است.
- triggerها برای `push` و `pull_request` عمومی هستند تا روی branchهای کاری هم اجرا شوند.
- YAML هر دو workflow به صورت local validate شده است.

### Secret Hygiene

- `.gitleaks.toml` اضافه شده است.
- فایل‌های env واقعی نباید commit شوند.
- placeholderهای مستندات در allowlist کنترل‌شده قرار دارند.
- history scan کامل هنوز باید در محیط امن انجام شود.

### Runbook و Docs

- runbook عملیاتی در `docs/OPERATIONS_RUNBOOK_FA.md` وجود دارد.
- خلاصه تثبیت در `docs/STABILIZATION_SUMMARY_FA.md` وجود دارد.
- index مستندات در `docs/INDEX_FA.md` وجود دارد.
- README و RUN_GUIDE به دلیل encoding نامطمئن در این فاز ویرایش نشده‌اند.

## چک‌لیست قبل از اولین Push/PR

- [ ] `git status` بررسی شده و فایل‌های تغییرکرده دسته‌بندی شده‌اند.
- [ ] فایل واقعی `.env` یا فایل local حساس در تغییرات وجود ندارد.
- [ ] مقدار واقعی secret، password، token یا connection string در diff وجود ندارد.
- [ ] backend tests با `python -m pytest -rs` pass شده‌اند.
- [ ] frontend lint با `npm.cmd run lint` pass شده است.
- [ ] frontend build با `npm.cmd run build` pass شده است.
- [ ] migrationها روی دیتابیس تست اجرا شده‌اند.
- [ ] نام دیتابیس integration شامل `test` یا `pytest` بوده است.
- [ ] Gitleaks local اجرا شده یا اگر نصب نیست، اجرای CI برای آن برنامه‌ریزی شده است.
- [ ] `docs/OPERATIONS_RUNBOOK_FA.md` review شده است.
- [ ] `docs/STABILIZATION_SUMMARY_FA.md` review شده است.
- [ ] `docs/RELEASE_READINESS_CHECKLIST_FA.md` review شده است.
- [ ] untrackedهای مربوط به فازهای قبلی آگاهانه نگه داشته یا stage شده‌اند.

## چک‌لیست اولین اجرای GitHub Actions

- [ ] workflow `CI` روی GitHub اجرا شده است.
- [ ] workflow `Security` روی GitHub اجرا شده است.
- [ ] backend job با PostgreSQL service بالا آمده است.
- [ ] envهای CI فقط dummy/test هستند و production نیستند.
- [ ] `python -m flask db upgrade` در backend job موفق شده است.
- [ ] `python -m pytest -rs` در backend job بدون skip غیرمنتظره pass شده است.
- [ ] frontend job از Node 22 استفاده کرده است.
- [ ] `npm ci` با lockfile موفق شده است.
- [ ] `npm run lint` موفق شده است.
- [ ] `npm run build` موفق شده است.
- [ ] Gitleaks با `.gitleaks.toml` اجرا شده و خروجی آن redacted است.

اگر backend job شکست خورد:

- PostgreSQL service، health check و نام دیتابیس `contractor_portal_pytest` را بررسی کنید.
- `DATABASE_URL` و `TEST_DATABASE_URL` را بررسی کنید و مطمئن شوید production نیستند.
- `FLASK_APP=wsgi.py` و working directory `backend` را بررسی کنید.
- مسیر تست‌ها باید `tests` باشد، نه `backend/tests` بعد از ورود به working directory backend.
- requirements و Python version را بررسی کنید.

اگر frontend job شکست خورد:

- Node version را بررسی کنید.
- وجود و صحت `frontend/package-lock.json` را بررسی کنید.
- `npm ci` را local بازتولید کنید.
- اگر build شکست خورد، خروجی Vite را بررسی کنید و API contract را بدون دلیل تغییر ندهید.

اگر Gitleaks شکست خورد:

- خروجی redacted را بررسی کنید.
- اگر secret واقعی پیدا شد، مقدار را چاپ نکنید و فوراً rotate کنید.
- false positive فقط با rule یا allowlist دقیق و محدود مدیریت شود.
- history rewrite یا force push فقط با تصمیم تیم انجام شود.

## چک‌لیست قبل از Staging

- [ ] دیتابیس staging ساخته و backup اولیه گرفته شده است.
- [ ] envهای staging از secret manager یا کانال امن تنظیم شده‌اند.
- [ ] `.env` واقعی staging وارد Git نشده است.
- [ ] `CORS_ALLOWED_ORIGINS` فقط originهای staging را allow می‌کند.
- [ ] migration روی staging اجرا شده و revision بررسی شده است.
- [ ] backend health و login تست شده‌اند.
- [ ] login پیمانکار آزمایشی تست شده است.
- [ ] login staff/admin تست شده است.
- [ ] import آزمایشی `codtafsiltamin` انجام شده است.
- [ ] import آزمایشی `contractors-1` انجام شده است.
- [ ] import آزمایشی `contractors-2` انجام شده است.
- [ ] rollback آزمایشی به batch موفق قبلی انجام شده است.
- [ ] dashboard پیمانکار بعد از import/rollback بررسی شده است.
- [ ] KPI service health با `GET /api/health` بررسی شده است.
- [ ] frontend production build deploy و smoke test شده است.
- [ ] secret scan روی branch اجرا شده است.

## چک‌لیست قبل از Production

- [ ] backup production گرفته و محل نگهداری امن آن مشخص شده است.
- [ ] migration در staging یا test DB با schema مشابه production تست شده است.
- [ ] rollback plan شامل source و batchهای هدف احتمالی آماده است.
- [ ] مسئول عملیات release مشخص است.
- [ ] زمان‌بندی انتشار و پنجره rollback مشخص است.
- [ ] اطلاع‌رسانی به کاربران داخلی انجام شده است.
- [ ] monitoring اولیه برای backend، frontend، DB و KPI آماده است.
- [ ] credentialهای demo در production استفاده نشده‌اند.
- [ ] `SECRET_KEY` و `JWT_SECRET_KEY` production قوی و جدا هستند.
- [ ] `KPI_API_KEY` production rotate و امن نگهداری شده است.
- [ ] CORS production فقط originهای واقعی را allow می‌کند.
- [ ] history scan در محیط امن اجرا شده یا تصمیم تیم برای زمان اجرای آن ثبت شده است.
- [ ] اگر secret قدیمی مشکوک وجود دارد، rotate انجام شده است.
- [ ] هیچ force push یا history rewrite بدون هماهنگی انجام نشده است.

## ریسک‌های باقی‌مانده

| ریسک | شدت | وضعیت | اقدام پیشنهادی |
|---|---:|---|---|
| اجرای واقعی GitHub Actions هنوز روی remote تایید نشده | متوسط | `gh` روی سیستم local نصب نیست و remote run بررسی نشد | پس از push/PR، صفحه Actions را بررسی و نتیجه را ثبت کنید |
| history scan کامل انجام نشده | متوسط/زیاد | Gitleaks local نصب نیست | اجرای `gitleaks detect --source . --redact --config .gitleaks.toml --log-opts="--all"` در محیط امن |
| README/RUN_GUIDE encoding نامطمئن دارند | متوسط | UTF-8 strict fail می‌شود و cp1256 decode می‌شود | فاز جدا برای backup، تبدیل کنترل‌شده encoding و diff review |
| rollback UI وجود ندارد | کم/متوسط | rollback API backend وجود دارد | طراحی UI فقط پس از تایید نیاز عملیاتی |
| purge/retention job پیاده‌سازی نشده | کم/متوسط | history فعلاً حفظ می‌شود | طراحی command با dry-run، backup prerequisite و audit |
| staging واقعی اجرا نشده | متوسط | فقط local validation انجام شده | ساخت staging و اجرای checklist staging |
| deployment production رسمی نشده | متوسط | runbook عملیاتی وجود دارد اما service/deploy target نهایی نیست | تدوین deployment plan شامل TLS، reverse proxy و monitoring |

## پیشنهاد فاز بعدی

1. Push branch و ایجاد PR برای اجرای واقعی `CI` و `Security` در GitHub Actions.
2. ثبت نتیجه اولین remote run در همین سند یا یک release note جدا.
3. اجرای history scan در محیط امن و تصمیم درباره rotate/history rewrite در صورت کشف secret واقعی.
4. اجرای فاز جدا برای اصلاح encoding README/RUN_GUIDE با backup و diff کنترل‌شده.
5. آماده‌سازی staging واقعی و اجرای کامل checklist staging.
6. تدوین deployment plan production شامل process manager، reverse proxy، TLS، monitoring و backup schedule.

