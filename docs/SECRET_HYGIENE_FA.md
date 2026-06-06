# راهنمای نگهداری امن Secretها و فایل‌های env

## اصل‌ها

- مقدار واقعی secret، password، token، API key و connection string نباید commit شود.
- فایل‌های `.env` فقط محلی هستند و باید در `.gitignore` باقی بمانند.
- فایل‌های example env فقط باید placeholder داشته باشند.
- برای production از secret manager، متغیرهای محیطی امن CI/CD، یا تنظیمات امن پلتفرم deploy استفاده شود.

## Placeholderهای مجاز

```text
<DB_HOST>
<DB_PORT>
<DB_NAME>
<DB_USER>
<DB_PASSWORD>
<DATABASE_URL>
<SECRET_KEY>
<JWT_SECRET_KEY>
<KPI_API_KEY>
<API_KEY>
```

## اجرای local

1. فایل example را کپی کنید.
2. مقدارهای placeholder را در فایل local `.env` جایگزین کنید.
3. فایل `.env` را commit نکنید.

نمونه:

```powershell
Copy-Item backend/config.example.env backend/.env
```

برای ساخت secret تصادفی:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Scriptها

Scriptهای loader باید password دیتابیس را از `PGPASSWORD` بگیرند. اگر `PGPASSWORD` تنظیم نشده باشد، script باید متوقف شود و از fallback hardcoded استفاده نکند.

## CI پیشنهادی

برای جلوگیری از ورود secret به repository، GitHub Actions با Gitleaks اضافه شده است:

```text
.github/workflows/security.yml
```

این job روی push و pull request اجرا می‌شود و در صورت پیدا کردن secret واقعی pipeline را fail می‌کند.

workflow کامل CI در فایل زیر جداگانه نگهداری می‌شود و backend tests، frontend lint و frontend build را اجرا می‌کند:

```text
.github/workflows/ci.yml
```

برای secret scanning همچنان `security.yml` مرجع اصلی است و نباید با jobهای runtime مخلوط شود.

## اجرای دستی scan روی working tree

```powershell
gitleaks detect --source . --redact --config .gitleaks.toml
```

گزینه `--redact` برای جلوگیری از چاپ مقدار واقعی secret در خروجی ضروری است.

## History scan

Scan روی working tree کافی نیست، چون ممکن است secret قبلاً در history گیت commit شده باشد. برای بررسی history، دستور زیر را در محیط امن اجرا کنید:

```powershell
gitleaks detect --source . --redact --config .gitleaks.toml --log-opts="--all"
```

اگر secret در history پیدا شد:

- مقدار secret را در گزارش عمومی چاپ نکنید.
- secret را فوراً rotate کنید.
- history rewrite فقط با تصمیم و هماهنگی تیم انجام شود.
- force push بدون هماهنگی ممنوع است.

## ابزارهای مکمل

ابزارهای مناسب برای آینده:

- Gitleaks
- TruffleHog
- GitHub Secret Scanning

قبل از commit فایل‌های docs/scripts/config sample همچنان با `rg` و review دستی بررسی شوند.
