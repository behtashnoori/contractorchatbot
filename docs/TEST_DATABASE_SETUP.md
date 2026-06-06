# راهنمای اجرای تست‌های Integration Backend

این پروژه برای تست‌های auth، RBAC و scope فاکتورها به یک دیتابیس PostgreSQL جدا از production نیاز دارد. بدون `TEST_DATABASE_URL`، تست‌های integration عمداً skip می‌شوند.

## 1. ساخت دیتابیس تست

در PowerShell، با کاربری که اجازه ساخت دیتابیس دارد:

```powershell
createdb <TEST_DB>
```

یا داخل `psql`:

```sql
CREATE DATABASE <TEST_DB>;
CREATE USER <TEST_USER> WITH PASSWORD '<TEST_PASSWORD>';
GRANT ALL PRIVILEGES ON DATABASE <TEST_DB> TO <TEST_USER>;
```

نام دیتابیس تست باید شامل `test` یا `pytest` باشد، مثل:

```text
contractorchatbot_test
```

این guard برای جلوگیری از اجرای تست‌ها روی دیتابیس production است.

## 2. تنظیم env تست

از مقدار واقعی secret، password یا connection string در repo استفاده نکنید. مقدار زیر فقط قالب placeholder است:

```powershell
cd backend
$env:TEST_DATABASE_URL="postgresql+psycopg://<TEST_USER>:<TEST_PASSWORD>@localhost:5432/<TEST_DB>"
```

برای اجرای migrationها روی دیتابیس تست:

```powershell
$env:DATABASE_URL=$env:TEST_DATABASE_URL
$env:SECRET_KEY="pytest-secret-key-at-least-32-characters-long"
$env:JWT_SECRET_KEY="pytest-jwt-secret-key-at-least-32-chars-long"
$env:CORS_ALLOWED_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
python -m flask db upgrade
```

## 3. اجرای تست‌ها

```powershell
python -m pytest
```

اگر `TEST_DATABASE_URL` تنظیم نشده باشد، تست‌های زیر skip می‌شوند:

- `backend/tests/test_auth_security.py`
- `backend/tests/test_invoice_access.py`

اگر نام دیتابیس داخل `TEST_DATABASE_URL` شامل `test` یا `pytest` نباشد، تست‌ها fail می‌شوند تا از اجرای ناخواسته روی دیتابیس production جلوگیری شود.

## اجرای تست در GitHub Actions

workflow زیر یک PostgreSQL service جدا با دیتابیس `contractor_portal_pytest` می‌سازد، migrationها را اجرا می‌کند و سپس تست‌های backend را با `python -m pytest -rs` اجرا می‌کند:

```text
.github/workflows/ci.yml
```

مقادیر env داخل این workflow فقط برای محیط CI و دیتابیس تست هستند و نباید برای production استفاده شوند.

## 4. سناریوهای پوشش داده شده

تست‌های integration فعلی این موارد را پوشش می‌دهند:

- login موفق و ناموفق
- جلوگیری از دسترسی contractor به endpointهای admin
- دسترسی staff به endpointهای staff/admin
- اثر تغییر role در درخواست بعدی
- مشاهده فاکتورهای خود پیمانکار
- جلوگیری از مشاهده فاکتور پیمانکار دیگر
- دسترسی staff به همه فاکتورها
- scope شدن گزینه‌های فیلتر فاکتور برای پیمانکار

## 5. نکات ایمنی

- از دیتابیس production برای `TEST_DATABASE_URL` استفاده نکنید.
- داده واقعی production را وارد دیتابیس تست نکنید.
- بعد از هر تست، رکوردهای ساخته‌شده توسط همان تست پاک می‌شوند، اما دیتابیس باید همچنان اختصاصی تست باقی بماند.
