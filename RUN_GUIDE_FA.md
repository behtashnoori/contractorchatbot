## راهنمای اجرای پروژه (Backend و Frontend)

این راهنما به صورت خیلی ساده و قدم‌به‌قدم توضیح می‌دهد چطور بک‌اند (Flask) و فرانت‌اند (Vite/React) را در ویندوز اجرا کنید. پیشنهاد می‌شود آن‌ها را در دو ترمینال جدا اجرا کنید.


### پیش‌نیازها
- **Python 3.11+**
- **Node.js 18+ (LTS)** و npm
- **PostgreSQL** (نسخه 12 یا بالاتر) - باید نصب و در حال اجرا باشد
- دسترسی به اینترنت برای نصب وابستگی‌ها


### 1) اجرای بک‌اند (Flask)
در یک ترمینال PowerShell باز کنید و دستورات زیر را اجرا کنید:

```powershell
cd backend

# ساخت و فعال‌سازی محیط مجازی پایتون
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# نصب وابستگی‌ها
pip install -r requirements.txt

# ساخت فایل تنظیمات از روی نمونه
Copy-Item -Path .\config.example.env -Destination .\.env -Force

# ⚠️ مهم: فایل .env را ویرایش کنید و اطلاعات اتصال PostgreSQL را تنظیم کنید:
# DATABASE_URL=postgresql+psycopg://username:password@host:port/database
# مثال: DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/contractorchatbot

# ساخت دیتابیس PostgreSQL (اگر وجود ندارد):
# در PostgreSQL: CREATE DATABASE contractorchatbot;

# اعمال مایگریشن‌ها و ساخت جداول
python -m flask db upgrade

# ساخت کاربران نمونه (پیمانکار و کارشناس)
python -m scripts.seed_demo_data

# اجرای سرور توسعه روی پورت انتخاب‌شده پروژه (3855)
# مقدار داخل .env هم تنظیم شده: FLASK_RUN_PORT=3855
python -m flask run --host=0.0.0.0
```

نکات:
- فایل `backend\.env` از روی `config.example.env` ساخته می‌شود. **حتماً** `DATABASE_URL` را با اطلاعات اتصال PostgreSQL خود تنظیم کنید.
- بعد از `flask db upgrade`، جداول در PostgreSQL ساخته می‌شوند.
- بعد از `seed_demo_data`، دو کاربر نمونه ساخته می‌شوند:
  - **پیمانکار**: username=`contractor`  password=`password123`
  - **کارشناس/ادمین**: username=`admin1`  password=`password123`
- بک‌اند روی پورت `3855` اجرا می‌شود (در `.env` تنظیم شده: `FLASK_RUN_PORT=3855`).


### 2) اجرای فرانت‌اند (Vite/React)
در یک ترمینال PowerShell جداگانه:

```powershell
cd frontend

# نصب وابستگی‌ها
npm install

# (اختیاری) اگر API روی آدرس دیگری است، فایل .env بسازید و این مقدار را تنظیم کنید
# مثل: echo VITE_API_BASE_URL=http://localhost:12345 > .env

# اجرای سرور توسعه
npm run dev
```

نکات:
- در این پروژه، Vite روی پورت ثابت `6902` اجرا می‌شود (در `vite.config.js` تنظیم شده است).
- برای اتصال فرانت‌اند به بک‌اند روی پورت `3855`، در حالت پیش‌فرض مقدار `VITE_API_BASE_URL` را روی `http://localhost:3855` قرار دهید (در `.env` فرانت‌اند).


### مشکلات رایج و رفع اشکال
- اگر `flask` متغیرهای `.env` را نشناخت: مطمئن شوید در پوشه `backend` هستید و `python-dotenv` نصب است (در `requirements.txt` وجود دارد). اجرای `python -m flask ...` را ترجیح دهید.
- اگر خطای اتصال به PostgreSQL دارید:
  - مطمئن شوید PostgreSQL در حال اجرا است
  - دیتابیس `contractorchatbot` را ساخته باشید: `CREATE DATABASE contractorchatbot;`
  - اطلاعات اتصال در `.env` را بررسی کنید (username, password, host, port, database)
- اگر جداول وجود ندارند: `python -m flask db upgrade` را اجرا کنید.
- اگر کاربران نمونه وجود ندارند: `python -m scripts.seed_demo_data` را اجرا کنید.
- اگر پورت‌ها اشغال هستند: برای بک‌اند از `--port` استفاده کنید؛ برای فرانت‌اند، Vite خودش پورت آزاد انتخاب می‌کند.
- در صورت خطای نصب پکیج‌های Node: ابتدا `npm cache verify` و سپس دوباره `npm install`.


### دستورات مفید
- اجرای مایگریشن‌ها (بک‌اند):
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m flask db upgrade
```

- ساخت نسخه Production فرانت‌اند:
```powershell
cd frontend
npm run build
```

- پیش‌نمایش نسخه Build شده:
```powershell
cd frontend
npm run preview
```


### اجرای سریع در دو ترمینال
- ترمینال 1 (بک‌اند):
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .\config.example.env .\.env -Force
# ⚠️ فایل .env را ویرایش کنید و DATABASE_URL را تنظیم کنید
python -m flask db upgrade
python -m scripts.seed_demo_data
# اجرای روی پورت 3855
python -m flask run --host=0.0.0.0
```

- ترمینال 2 (فرانت‌اند):
```powershell
cd frontend
npm install
# (اختیاری) اتصال صریح به بک‌اند روی 3855
# echo VITE_API_BASE_URL=http://localhost:3855 > .env
npm run dev
```

تمام! بک‌اند روی `http://localhost:3855` و فرانت‌اند روی `http://localhost:6902` بالا می‌آید.


