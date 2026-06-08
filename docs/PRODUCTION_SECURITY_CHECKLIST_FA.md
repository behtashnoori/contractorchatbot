# چک‌لیست امنیتی Production

این سند برای بازبینی نهایی قبل از staging/production است. مقدار واقعی secret، password،
connection string یا token نباید در این سند، لاگ، audit یا repository ذخیره شود.

## 1. Env و secretها

- `SECRET_KEY` اجباری است و برنامه بدون مقدار معتبر start نمی‌شود.
- `JWT_SECRET_KEY` یا alias آن `JWT_SECRET` اجباری است و باید جدا از `SECRET_KEY` باشد.
- هر دو secret باید مقدار تصادفی قوی، حداقل 32 کاراکتر و غیر placeholder باشند.
- `DATABASE_URL` اجباری است و باید فقط از secret manager یا env امن deploy خوانده شود.
- `backend/config.example.env` فقط placeholder دارد و نباید برای production copy مستقیم شود.
- برای production، `FLASK_ENV=production` و `FLASK_DEBUG=0` الزامی است.

## 2. CORS

- `CORS_ALLOWED_ORIGINS` اجباری است.
- در production فقط origin دقیق frontend با HTTPS مجاز است.
- wildcard مانند `*` نباید استفاده شود.
- originهای local فقط برای توسعه مجاز هستند.
- بعد از deploy، درخواست از origin غیرمجاز باید بدون header `Access-Control-Allow-Origin` رد شود.

## 3. JWT و auth

- authorization از role فعلی دیتابیس خوانده می‌شود، نه از claim داخل token.
- اگر user حذف شود، token قدیمی نباید به endpointهای محافظت‌شده دسترسی بدهد.
- اگر contractor لینک‌شده inactive شود، access token و refresh token قدیمی نباید ادامه پیدا کنند.
- زمان انقضای access token کوتاه نگه داشته شود؛ مقدار نمونه فعلی 900 ثانیه است.
- refresh token باید مدت محدود داشته باشد؛ مقدار نمونه فعلی 604800 ثانیه است.
- برای فاز بعدی، token rotation یا session revocation قابل ردیابی طراحی شود.

## 4. Password policy

- تولید password پیمانکار فعلا از کدهای قابل حدس انجام می‌شود؛ این ریسک برای production باقی است.
- تا قبل از production واقعی، password پیمانکار باید تصادفی، یک‌بارمصرف و از کانال امن تحویل شود.
- تغییر runtime بزرگ برای password flow در این فاز انجام نشده، چون contractor change-password فعلا فعال نیست.
- برای staff/admin، password باید قوی و خارج از repository مدیریت شود.
- credentialهای demo فقط برای local/test هستند و باید در production ممنوع و rotate شوند.

## 5. Login و rate limiting

- rate limiting اپلیکیشنی برای `/auth/login` فعلا اضافه نشده است.
- افزودن dependency یا middleware جدید در این فاز انجام نشد تا auth flow کم‌ریسک بماند.
- قبل از production، یکی از این دو راه باید اجرا شود:
  - rate limit در reverse proxy/WAF برای `/auth/login` و `/auth/refresh`
  - یا rate limiter backend با storage مناسب و تست‌شده
- لاگ login ناموفق نباید password یا token را ذخیره کند.

## 6. Rollback access

- rollback فقط با `@require_staff` قابل دسترسی است.
- role در هر request از دیتابیس تازه خوانده می‌شود.
- contractor یا staff demote‌شده با token قدیمی نباید rollback کند.
- rollback موفق و ناموفق در `AuditLog` ثبت می‌شود.
- response rollback نباید password، token، connection string یا payload حساس برگرداند.

## 7. Token storage frontend

- access token و refresh token فعلا در `localStorage` ذخیره می‌شوند.
- این در برابر XSS ریسک متوسط/زیاد دارد، مخصوصا برای refresh token.
- مهاجرت به HttpOnly Secure SameSite cookie در این فاز انجام نشده، چون نیازمند تغییر auth flow و CORS credentials است.
- قبل از production واقعی، یکی از گزینه‌های زیر باید تصمیم‌گیری شود:
  - HttpOnly cookie برای refresh token
  - token rotation و کاهش عمر refresh token
  - CSP سخت‌تر و مانیتورینگ XSS

## 8. Audit log

- `AuditLog` فقط `user_id`, `action`, `entity`, `entity_id`, `created_at` ذخیره می‌کند.
- audit نباید password، token، filename واقعی یا payload حساس ذخیره کند.
- login، import upload و rollback ثبت می‌شوند.
- برای فاز بعدی، metadata ساختاریافته فقط در صورت redaction روشن و نیاز عملیاتی اضافه شود.

## 9. Backup security

- قبل از migration یا import بزرگ production، backup کامل گرفته شود.
- restore باید ابتدا در staging تمرین شود.
- backupها باید encrypted و با دسترسی محدود نگهداری شوند.
- connection string یا dump production نباید وارد test logs یا repository شود.

## 10. Secret scanning و history scan

- `.gitleaks.toml` و workflow امنیتی برای scan وجود دارد.
- allowlist فقط باید placeholderهای مستند را پوشش دهد.
- قبل از production، history scan کامل با Gitleaks روی همه branch/tagها اجرا شود.
- اگر secret واقعی در history پیدا شد، ابتدا secret rotate شود؛ history rewrite فقط با تصمیم تیم انجام شود.

## 11. Demo credentials

- `backend/scripts/seed_demo_data.py` فقط برای local/test است.
- credentialهای demo نباید در production ایجاد یا استفاده شوند.
- اگر demo seed اشتباها روی محیط غیرتستی اجرا شد، همه userهای demo باید حذف یا password آنها rotate شود.
- docs باید همیشه demo credential را با هشدار local/test نشان دهند، نه به‌عنوان credential production.

## 12. چک‌لیست قبل از Production

- [ ] `FLASK_ENV=production` و `FLASK_DEBUG=0` تنظیم شده است.
- [ ] `SECRET_KEY` و `JWT_SECRET_KEY` قوی، جدا و خارج از repo هستند.
- [ ] `DATABASE_URL` به دیتابیس production درست اشاره می‌کند و در لاگ چاپ نمی‌شود.
- [ ] `CORS_ALLOWED_ORIGINS` فقط originهای HTTPS واقعی را دارد.
- [ ] origin غیرمجاز smoke test شده و CORS header دریافت نمی‌کند.
- [ ] login ناموفق و brute force با rate limit در proxy/WAF یا backend کنترل شده است.
- [ ] refresh token strategy برای production تایید شده است.
- [ ] هیچ credential demo در production فعال نیست.
- [ ] backup و restore plan تست شده است.
- [ ] rollback با user staff/admin تست شده و با contractor رد شده است.
- [ ] audit log برای login/import/rollback بررسی شده و secret ذخیره نمی‌کند.
- [ ] Gitleaks روی working tree و git history اجرا شده است.
- [ ] backend tests، frontend lint و frontend build سبز هستند.

## ریسک‌های باقی‌مانده

- نبود rate limiting داخلی برای login.
- نگهداری refresh token در `localStorage`.
- password پیمانکار قابل حدس تا زمان بازطراحی password/reset flow.
- نبود session revocation/token rotation ساختاریافته.
- نیاز به deployment plan نهایی شامل TLS، reverse proxy، monitoring و alerting.
