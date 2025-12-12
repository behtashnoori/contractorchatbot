# Contractor Chatbot

سیستم مدیریت پیمانکاران و فاکتورها با رابط کاربری مدرن

## 📋 درباره پروژه

این پروژه یک سیستم مدیریت پیمانکاران و فاکتورها است که شامل:
- **Backend**: Flask REST API با PostgreSQL
- **Frontend**: React + Vite + Material-UI
- **API**: API جداگانه برای گزارش‌گیری و KPI

## 🏗️ ساختار پروژه

```
contractorchatbot/
├── backend/          # Flask Backend API
├── frontend/         # React Frontend
├── api/              # API جداگانه برای گزارش‌گیری
├── db/               # اسکریپت‌های دیتابیس و SQL
├── data/             # فایل‌های داده نمونه
├── docs/             # مستندات پروژه
└── scripts/          # اسکریپت‌های کمکی
```

## 🚀 راه‌اندازی سریع

برای راهنمای کامل اجرا، فایل [RUN_GUIDE_FA.md](./RUN_GUIDE_FA.md) را مطالعه کنید.

### پیش‌نیازها

- Python 3.11+
- Node.js 18+ (LTS)
- PostgreSQL 12+
- npm یا yarn

### نصب و اجرا

#### 1. Backend (Flask)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .\config.example.env .\.env -Force
# ویرایش فایل .env و تنظیم DATABASE_URL
python -m flask db upgrade
python -m scripts.seed_demo_data
python -m flask run --host=0.0.0.0
```

Backend روی `http://localhost:3855` اجرا می‌شود.

#### 2. Frontend (React)

```powershell
cd frontend
npm install
npm run dev
```

Frontend روی `http://localhost:8308` اجرا می‌شود.

## 👤 کاربران پیش‌فرض

بعد از اجرای `seed_demo_data`، کاربران زیر ایجاد می‌شوند:

- **پیمانکار**: `contractor` / `password123`
- **کارشناس/ادمین**: `admin1` / `password123`

## 🛠️ تکنولوژی‌ها

### Backend
- Flask 3.0
- SQLAlchemy
- Flask-Migrate
- Flask-JWT-Extended
- PostgreSQL
- Pandas
- OpenPyXL

### Frontend
- React 19
- Vite
- Material-UI (MUI)
- React Router
- TanStack Query
- Axios
- Day.js + JalaliDay

## 📁 ساختار دیتابیس

پروژه از PostgreSQL استفاده می‌کند. برای جزئیات بیشتر به پوشه `db/sql/` مراجعه کنید.

## 📝 مستندات

- [راهنمای اجرا](./RUN_GUIDE_FA.md)
- [مستندات API](./docs/api-design.md)
- [طرح Backend](./docs/backend-plan.md)
- [طرح Frontend](./docs/frontend-plan.md)
- [خط لوله Import](./docs/import-pipeline.md)

## 🔧 اسکریپت‌های کمکی

- `scripts/seed_demo_data.py` - ایجاد کاربران نمونه
- `scripts/check_database_counts.py` - بررسی تعداد رکوردها
- `scripts/test_login.py` - تست لاگین

## 📄 لایسنس

این پروژه برای استفاده داخلی است.

## 🤝 مشارکت

برای مشارکت در پروژه، لطفاً ابتدا یک Issue ایجاد کنید یا با تیم توسعه تماس بگیرید.

