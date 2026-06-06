# گزارش معماری و وضعیت پروژه Contractor Chatbot

تاریخ بررسی: 2026-06-02  
دامنه بررسی: کل repository شامل `backend/`، `frontend/`، `api/`، `db/`، `scripts/`، `docs/` و فایل‌های راهنما.  
اصل محرمانگی: مقدار واقعی secret، password، token، connection string و کلیدها در این گزارش نوشته نشده است. فقط نام متغیرها و محل مشاهده ذکر شده‌اند.

---

## 1. خلاصه مدیریتی پروژه

این پروژه یک وب‌اپ اطلاع‌رسانی وضعیت فاکتورها/صورتحساب‌های پیمانکاران است. پیمانکار بعد از ورود، فهرست فاکتورهای مربوط به خود، وضعیت، مبالغ، تاریخ‌های کلیدی و جزئیات هر روکش/فاکتور را می‌بیند. کاربر داخلی یا staff/admin می‌تواند علاوه بر مشاهده سراسری فاکتورها، داده‌ها را از فایل‌های Excel وارد کند و وضعیت import را پیگیری کند.

کاربران اصلی:

- پیمانکار: مشاهده وضعیت فاکتورهای خودش.
- کارشناس/ادمین داخلی: بارگذاری فایل‌های داده، مشاهده کل داده‌ها، ایجاد کاربر برای پیمانکار، بررسی خطاهای import.
- مصرف‌کننده گزارش KPI: از microservice جداگانه `api/` برای گزارش سالانه و export استفاده می‌کند.

مسئله‌ای که سیستم حل می‌کند، کاهش مراجعات دستی پیمانکاران برای اطلاع از وضعیت فاکتور، پرداخت یا صورتحساب و متمرکز کردن اطلاعات واردشده از فایل‌های عملیاتی است.

وضعیت فعلی پروژه: **در حال توسعه و نیازمند تثبیت قبل از بهره‌برداری جدی**. دلیل: مسیرهای اصلی backend و frontend وجود دارند و build فرانت موفق است، اما lint فرانت fail می‌شود، importها rollback کامل ندارند، چند مسیر مستندات دارای مقدار نمونه حساس هستند، و حداقل یک ناسازگاری مهم بین مدل و importer دیده شد.

---

## 2. تکنولوژی‌ها و ساختار کلی

### Backend اصلی

- زبان: Python
- فریم‌ورک: Flask 3
- ORM: Flask-SQLAlchemy / SQLAlchemy
- Migration: Flask-Migrate / Alembic
- Auth: Flask-JWT-Extended با access و refresh token
- Password hashing: Flask-Bcrypt
- CORS: Flask-CORS با originهای اجباری از env
- فایل Excel: pandas و openpyxl
- تاریخ شمسی: `convertdate`
- دیتابیس: PostgreSQL

### Frontend

- React 19
- Vite
- Material UI / MUI
- React Router
- TanStack Query
- Axios
- dayjs + jalaliday

### API گزارش‌گیری جداگانه

پوشه `api/` یک Flask app جدا برای KPI است که با `psycopg2` مستقیم به PostgreSQL وصل می‌شود و endpointهای `/api/kpi/yearly` و export دارد. این بخش از backend اصلی جداست و auth آن API key مستقل است.

### ابزارهای تست، lint، build و deploy

- Backend test: `pytest` در `backend/tests/`
- Frontend lint: `npm run lint`
- Frontend build: `npm run build`
- Backend run: `python -m flask run`
- Frontend dev: `npm run dev`
- Deploy: فایل deploy مشخصی مثل Dockerfile، compose، CI pipeline یا service unit در repository دیده نشد؛ **نیازمند بررسی بیشتر**.

### ساختار پوشه‌ها

| مسیر | مسئولیت |
|---|---|
| `backend/` | Flask API اصلی، مدل‌ها، routeها، migrationها، serviceهای import و تست‌های backend |
| `frontend/` | اپ React/Vite، صفحات پیمانکار و ادمین، clientهای API |
| `api/` | microservice گزارش KPI و export CSV/XLSX |
| `db/sql/` | اسکریپت‌های SQL قدیمی/تحلیلی برای schema، staging، upsert، view و گزارش |
| `data/` | فایل‌های Excel نمونه یا داده ورودی |
| `docs/` | طراحی API، backend، frontend، import و security/ops |
| `scripts/` | اسکریپت‌های load مستقیم به PostgreSQL برای داده‌های Excel/CSV |

---

## 3. معماری Backend

### فایل‌ها و ماژول‌های اصلی

- `backend/app/__init__.py`: factory برنامه، validate محیط، init extensionها، register blueprintها، error handlerها، CORS و security header.
- `backend/app/config.py`: خواندن envها و تنظیمات Flask/DB/JWT/upload.
- `backend/app/extensions.py`: تعریف singletonهای `db`, `migrate`, `jwt`, `bcrypt`, `cors`.
- `backend/app/models/__init__.py`: مدل‌های دیتابیس.
- `backend/app/routes/auth.py`: login، refresh، me، change-password.
- `backend/app/routes/invoices.py`: فهرست فاکتورها، جزئیات روکش، گزینه‌های فیلتر.
- `backend/app/routes/admin.py`: upload فایل‌ها، progress import، template download، لیست داده‌ها و ایجاد user پیمانکار.
- `backend/app/services/*_importer.py`: منطق import از Excel.
- `backend/app/utils/auth_decorators.py`: دکوریتور JWT و staff/admin.
- `backend/app/utils/auth_utils.py`: تولید/نرمال‌سازی username و password پیمانکار، resolve user از JWT و RBAC.
- `backend/app/services/audit_log.py`: audit trail سبک برای login، view invoice و upload import.

### مدل‌های اصلی دیتابیس

| مدل | نقش |
|---|---|
| `Contractor` | اطلاعات پیمانکار/تامین‌کننده شامل کد تفصیلی، کد تامین‌کننده، نام، وضعیت و نوع |
| `User` | کاربر سیستم، hash رمز، نقش، اتصال اختیاری به پیمانکار |
| `InvoiceSummary` | داده خلاصه فاکتور/روکش شامل شماره روکش، وضعیت، تاریخ‌ها، مبالغ، کارفرما و کدهای پیمانکار |
| `InvoiceDetail` | ردیف‌های جزئیات فاکتور/روکش شامل شماره سند، تاریخ، تامین‌کننده، عنوان قلم، مبلغ و توضیحات |
| `ImportBatch` | batchهای import با source، status، progress و metrics |
| `ImportError` | خطاهای ردیفی import همراه payload همان ردیف |
| `AuditLog` | ثبت رویدادهای کلیدی بدون payload حساس |

### رابطه بین مدل‌ها

- `User.contractor_id -> Contractor.id`: هر پیمانکار می‌تواند یک یا چند user داشته باشد.
- `InvoiceSummary.contractor_id -> Contractor.id`: خلاصه فاکتور می‌تواند به پیمانکار وصل شود.
- `InvoiceDetail.contractor_id -> Contractor.id`: جزئیات هم می‌تواند به پیمانکار وصل شود.
- `InvoiceSummary.last_update_batch_id -> ImportBatch.id`
- `InvoiceDetail.last_update_batch_id -> ImportBatch.id`
- `ImportError.batch_id -> ImportBatch.id`
- `AuditLog.user_id -> User.id`
- رابطه view-only بین `InvoiceSummary` و `InvoiceDetail` از طریق `cover_number` تعریف شده است.

### APIها و endpointهای مهم

#### احراز هویت

| مسیر | متد | ورودی مهم | خروجی | نقش مجاز | فایل/تابع |
|---|---|---|---|---|---|
| `/auth/login` | POST | `username`, `password` | `access_token`, `refresh_token`, `must_change_password`, contractor summary | عمومی | `backend/app/routes/auth.py::login` |
| `/auth/refresh` | POST | refresh JWT در header | access token جدید | کاربر دارای refresh token معتبر | `auth.py::refresh` |
| `/auth/me` | GET | access JWT | اطلاعات user، contractor و totals | کاربر login شده | `auth.py::me` |
| `/auth/change-password` | POST | `current_password`, `new_password` | `status=password_updated` | فقط staff/admin | `auth.py::change_password` |

نکته: contractor اجازه تغییر رمز از این endpoint ندارد.

#### پنل پیمانکار / وضعیت فاکتورها

| مسیر | متد | ورودی مهم | خروجی | نقش مجاز | فایل/تابع |
|---|---|---|---|---|---|
| `/invoices/` | GET | `page`, `page_size`, `status`, `cover_number`, `search`, `fiscal_year` | paging، totals، items شامل شماره روکش، وضعیت، مبلغ، تاریخ‌ها، تعداد detail | contractor فقط داده خودش؛ staff/admin همه | `backend/app/routes/invoices.py::list_invoices` |
| `/invoices/<cover_number>` | GET | `cover_number` | summary و details روکش | contractor فقط داده خودش؛ staff/admin همه | `invoices.py::invoice_detail` |
| `/invoices/filters/options` | GET | `fiscal_year`, `status` | سال‌های مالی، وضعیت‌ها و آمار فیلتر | contractor scoped؛ staff/admin همه | `invoices.py::get_filter_options` |

#### پنل ادمین / import و داده‌ها

| مسیر | متد | ورودی مهم | خروجی | نقش مجاز | فایل/تابع |
|---|---|---|---|---|---|
| `/admin/uploads` | POST | multipart files | placeholder batch | staff/admin | `admin.py::upload_batch` |
| `/admin/uploads/codtafsiltamin` | POST | multipart `file` | batch و metrics | staff/admin | `admin.py::upload_codtafsiltamin` |
| `/admin/uploads/contractors-1` | POST | multipart `file` | `202`، batch pending | staff/admin | `admin.py::upload_contractors_one` |
| `/admin/uploads/contractors-2` | POST | multipart `file` | `202`، batch pending | staff/admin | `admin.py::upload_contractors_two` |
| `/admin/uploads/<batch_id>/progress` | GET | UUID batch | status، terminal، progress، metrics | staff/admin | `admin.py::get_upload_progress` |
| `/admin/uploads/<batch_id>` | GET | UUID batch | batch summary و errors | staff/admin | `admin.py::batch_status` |
| `/admin/templates/codtafsiltamin` | GET | - | Excel template | staff/admin | `admin.py::download_codtafsiltamin_template` |
| `/admin/templates/contractors-1` | GET | - | Excel template | staff/admin | `admin.py::download_contractors_one_template` |
| `/admin/templates/contractors-2` | GET | - | Excel template | staff/admin | `admin.py::download_contractors_two_template` |
| `/admin/contractors` | GET | `page`, `per_page`, `search` | paging پیمانکاران | staff/admin | `admin.py::list_contractors` |
| `/admin/contractors/<contractor_id>/create-user` | POST | UUID پیمانکار | username و password تولیدشده | staff/admin | `admin.py::create_contractor_user` |
| `/admin/invoice-summaries` | GET | `page`, `per_page`, `search` | paging خلاصه‌ها | staff/admin | `admin.py::list_invoice_summaries` |
| `/admin/invoice-details` | GET | `page`, `per_page`, `search` | paging جزئیات | staff/admin | `admin.py::list_invoice_details` |

#### API گزارش KPI جداگانه

| مسیر | متد | ورودی مهم | خروجی | نقش/حفاظت | فایل/تابع |
|---|---|---|---|---|---|
| `/api/health` | GET | - | `{status: ok}` | عمومی | `api/app.py::health` |
| `/api/kpi/yearly` | GET | `supplier_uid` یا `supplier_name`, `source`, `year`, `limit`, `offset` | rows KPI | API key | `api/app.py::kpi_yearly` |
| `/api/kpi/yearly/export` | GET | همان + `format=csv|xlsx` | فایل export | API key | `api/app.py::export_kpi_yearly` |
| `/kpi` | GET | queryهای KPI | HTML report | API key | `api/app.py::kpi_page` |

---

## 4. معماری Frontend

### صفحات اصلی

- `LandingPage.jsx`: صفحه ورود/معرفی اولیه.
- `LoginPage.jsx`: فرم login و انتقال کاربر بعد از ورود.
- `DashboardPage.jsx`: داشبورد فاکتورها برای پیمانکار یا staff.
- `InvoiceDetailPage.jsx`: جزئیات یک روکش/فاکتور.
- `AdminUploadPage.jsx`: upload فایل‌ها، templateها، progress، error list و مرور داده‌های import شده برای staff/admin.

### routeها

در `frontend/src/App.jsx`:

- `/` -> landing
- `/login` -> login
- `/invoices` -> protected dashboard
- `/invoice/:coverNumber` -> protected invoice detail
- `/admin/uploads` -> protected admin upload page
- `*` -> landing

توجه: route ادمین در `ProtectedRoute` فقط login بودن را چک می‌کند؛ خود `AdminUploadPage` با `hasStaffAccess` کاربر غیر staff را redirect می‌کند. backend هم staff/admin را enforce می‌کند.

### کامپوننت‌های مهم

- `AuthProvider.jsx`: bootstrap session از token، login/logout و profile state.
- `ProtectedRoute.jsx`: guard برای routeهای نیازمند login.
- `AppLayout.jsx`: layout اصلی، nav، logout و لینک admin برای staff.
- `InvoicesTable.jsx`: نمایش جدول/کارت فاکتورها و pagination.
- `FiltersBar.jsx`: جستجو و فیلتر status.
- `SummaryCard.jsx`: کارت خلاصه.
- `ErrorBoundary.jsx`: fallback خطای UI.

### تجربه پیمانکار بعد از ورود

پیمانکار وارد `/invoices` می‌شود و موارد زیر را می‌بیند:

- فهرست فاکتورهای scope شده به خودش.
- فیلتر بر اساس سال مالی و وضعیت.
- جستجو بر اساس شماره روکش/اتوماتسیون/بهره‌بردار.
- مبلغ ناخالص، مبلغ خالص، وضعیت، تاریخ ایجاد و تاریخ‌های تحویل.
- امکان باز کردن جزئیات روکش در `/invoice/:coverNumber`.

### امکانات staff/admin

- مشاهده همه فاکتورها در dashboard.
- ورود به `/admin/uploads`.
- upload سه منبع Excel: `codtafsiltamin`، `contractors-1`، `contractors-2`.
- دانلود templateهای Excel.
- مشاهده progress و خطاهای batch.
- مشاهده لیست پیمانکاران، خلاصه فاکتورها و جزئیات import شده.
- ایجاد user پیمانکار از روی contractor.

### اتصال Frontend به Backend

- `frontend/src/api/client.js` یک axios client می‌سازد.
- اگر `VITE_API_BASE_URL` تعریف شده باشد، همان استفاده می‌شود.
- اگر hostname محلی باشد، پیش‌فرض `http://localhost:8000` است.
- در شبکه داخلی، frontend از hostname فعلی با port 8000 استفاده می‌کند.
- token در interceptor به header `Authorization: Bearer ...` اضافه می‌شود.
- در 401، refresh token برای گرفتن access token جدید استفاده می‌شود و درخواست retry می‌شود.

### مدیریت token، session، خطا و loading

- access و refresh token هر دو در `localStorage` ذخیره می‌شوند.
- `AuthProvider` هنگام mount، اگر access token وجود داشته باشد `/auth/me` را فراخوانی می‌کند.
- در refresh شکست‌خورده، localStorage پاک می‌شود و کاربر به `/login` منتقل می‌شود.
- loading در `ProtectedRoute`، `DashboardPage` و `InvoiceDetailPage` با spinner نمایش داده می‌شود.
- خطاها معمولاً با MUI `Alert` نمایش داده می‌شوند.
- ریسک: نگهداری refresh token در localStorage در برابر XSS حساس است.
- ریسک کیفیت: console logهای متعدد در فایل‌های dashboard/detail/admin/protected route وجود دارد.

---

## 5. منطق کسب‌وکار سیستم فاکتورها

### چرخه داده فاکتور

چرخه اصلی در کد به این شکل است:

1. فایل پیمانکاران/تامین‌کنندگان از منبع `codtafsiltamin` وارد می‌شود و جدول `Contractor` را می‌سازد.
2. فایل `contractors-1` خلاصه فاکتورها/روکش‌ها را وارد `InvoiceSummary` می‌کند.
3. فایل `contractors-2` ردیف‌های جزئیات فاکتور را وارد `InvoiceDetail` می‌کند.
4. پیمانکار با user خود وارد می‌شود و بر اساس `detail_code` و `supplier_code` فقط داده scope شده را می‌بیند.
5. staff/admin همه داده‌ها را می‌بیند و import را مدیریت می‌کند.

### وضعیت‌های احتمالی فاکتور

کد وضعیت‌ها را enum سخت‌گیرانه نکرده و مقدار status از فایل‌ها می‌آید. مقادیر مشاهده‌شده/پشتیبانی‌شده در UI و backend شامل این‌هاست:

- تایید شده / approved
- ثبت شده / registered
- در انتظار / جاری / pending
- معلق
- رد شده / عودت شده / rejected
- نامشخص

نیازمند بررسی بیشتر: یکسان‌سازی املای فارسی/عربی و enum رسمی وضعیت‌ها.

### import فایل‌ها

منابع import:

- `codtafsiltamin`: دایرکتوری پیمانکار/تامین‌کننده.
- `contractors-1`: خلاصه فاکتورها/روکش‌ها.
- `contractors-2`: جزئیات ردیف‌های فاکتور.

محل upload:

- `frontend/src/pages/AdminUploadPage.jsx`
- endpointهای `/admin/uploads/*`

ستون‌های لازم:

- `codtafsiltamin`: کد تامین‌کننده، نام تامین‌کننده، وضعیت، نوع، کد تفصیلی.
- `contractors-1`: در کد فقط `cover_number` و `invoice_status` اجباری هستند؛ ستون‌های دیگر با mapping مبتنی بر tokenهای فارسی خوانده می‌شوند.
- `contractors-2`: `cover_number`، `invoice_date`، `supplier_name`، `gross_amount` اجباری هستند.

اعتبارسنجی:

- `codtafsiltamin` headerهای مورد انتظار را validate می‌کند.
- `contractors-1` با `HEADER_RULES` ستون‌ها را map می‌کند و نبود keyهای اجباری را خطا می‌دهد.
- `contractors-2` با `COLUMN_ALIASES` ستون‌ها را resolve می‌کند و نبود required fieldها را خطا می‌دهد.
- مقادیر تاریخ و عدد با helperهای `parse_jalali` و `parse_decimal` normalize می‌شوند.

رفتار خطا:

- خطای header/read باعث `ValueError` و failed شدن batch می‌شود.
- خطای ردیفی در بسیاری از مسیرها به `ImportError` تبدیل می‌شود.
- خطاهای import با `batch_id` قابل مشاهده‌اند.

تراکنشی بودن و rollback:

- importها قبل از درج داده جدید، داده‌های قبلی را حذف و commit می‌کنند.
- processing به صورت batch/bulk commit انجام می‌شود.
- بنابراین import کامل atomic نیست و rollback سراسری برای بازگرداندن dataset قبلی وجود ندارد.
- این موضوع برای بهره‌برداری ریسک زیاد دارد.

---

## 6. احراز هویت و سطح دسترسی

### مکانیزم login

- login با username/password در `/auth/login`.
- password با bcrypt hash مقایسه می‌شود.
- access token و refresh token با Flask-JWT-Extended صادر می‌شود.
- identity توکن `user.id.hex` است.
- در هر درخواست محافظت‌شده، user از دیتابیس دوباره load می‌شود.

### نقش‌ها

- `contractor`
- `staff`
- `admin`

`staff` و `admin` دسترسی داخلی/عملیاتی دارند. تابع backend: `user_has_staff_access`.

### scope پیمانکار

در endpointهای invoice، پیمانکار از طریق `detail_code` و در صورت وجود `supplier_code` scope می‌شود. برای staff/admin محدودیت برداشته می‌شود.

نکته امنیتی مهم: در `_invoice_summary_base_query_for_user` یک fallback از طریق `InvoiceDetail.cover_number` وجود دارد که اگر `supplier_code` خالی یا `NULL` باشد، ممکن است به نمایش summary خارج از `detail_code` کمک کند. این رفتار ظاهراً برای داده ناقص طراحی شده، اما باید با تست‌های بیشتر روی داده واقعی بررسی شود.

### نقاط حساس امنیتی

- ذخیره refresh token در localStorage.
- تولید password پیمانکار بر اساس کدهای قابل حدس.
- نمایش password تولیدشده در پاسخ `/admin/contractors/<id>/create-user`، هرچند با توضیح «فقط یکبار».
- مستندات و اسکریپت‌ها دارای مقدار نمونه/پیش‌فرض password یا connection هستند؛ در این گزارش مقدارها عمداً redacted شده‌اند.
- console logهای frontend ممکن است جزئیات response، progress یا داده‌های فاکتور را در browser console نمایش دهند.
- نبود rate limiting برای login.
- نبود سیاست lockout یا throttling.

---

## 7. دیتابیس و داده‌ها

### جدول‌ها/مدل‌های اصلی

#### `contractor`

فیلدهای مهم:

- `id` UUID PK
- `detail_code` unique/index
- `supplier_code` index
- `name`
- `status`
- `type`
- `relationship_start`
- `raw_payload`
- timestamps

#### `user`

- `id` UUID PK
- `username` unique/index
- `password_hash`
- `must_change_password`
- `last_login_at`
- `contractor_id` FK nullable
- `role`

#### `invoicesummary`

- `id` UUID PK
- `contractor_id` FK nullable
- `detail_code`, `supplier_code`
- `automation_number`
- `invoice_created_at`, `delivered_to_accounting_at`, `delivered_to_supervisor_at`, `invoice_date`
- `cover_number`
- `business_owner`, `cost_subject`
- `gross_amount`, `net_amount`
- `invoice_status`
- `notes`
- `contractor_invoice_no`, `permit_number`, `permit_type`
- `client_contract_number`, `client_name`
- `raw_payload`
- `last_update_batch_id` FK

#### `invoicedetail`

- `id` UUID PK
- `contractor_id` FK nullable
- `detail_code`, `supplier_code`
- `invoice_no`, `invoice_date`
- `unit_code`, `supplier_name`
- `status`, `item_title`
- `gross_amount`
- `reference`, `description`
- `cover_number`
- `raw_payload`
- `last_update_batch_id` FK

#### `importbatch`

- `id` UUID PK
- `name`, `source`, `status`, `uploaded_by`, `notes`
- `total_rows`, `rows_processed`, `progress_percentage`
- `inserted_count`, `updated_count`, `errors_count`

#### `importerror`

- `id` UUID PK
- `batch_id` FK
- `source_file`
- `row_index`
- `message`
- `payload`

#### `auditlog`

- `id` UUID PK
- `user_id` FK nullable
- `action`
- `entity`
- `entity_id`
- `created_at`

### Migration

در `backend/migrations/versions/` migrationهای زیر دیده شد:

- initial tables
- progress tracking برای `ImportBatch`
- ستون `role` در `User`
- جدول `AuditLog`
- normalize وضعیت‌های import batch به `pending/processing/done/failed`

وضعیت واقعی دیتابیس محیط جاری اجرا نشد؛ نیازمند بررسی بیشتر با اتصال `DATABASE_URL` واقعی و `flask db current`.

### seed data

`backend/scripts/seed_demo_data.py` کاربر پیمانکار و staff/expert نمونه می‌سازد. مقدار passwordهای demo در این گزارش نوشته نشده است. برای production نباید از داده demo استفاده شود.

### وابستگی به Excel/فایل/دیتابیس خارجی

- import عملیاتی به Excel وابسته است.
- `data/` شامل فایل‌های نمونه Excel است.
- `scripts/` اسکریپت‌های load مستقیم به PostgreSQL دارد.
- microservice `api/` به PostgreSQL و view `public.v_kpi_yearly_compact` وابسته است.

---

## 8. اجرای پروژه

### Backend

پیش‌نیاز:

- Python 3.11+ طبق README؛ در محیط بررسی Python 3.13.9 هم برای pytest استفاده شد.
- PostgreSQL
- virtualenv

دستورات معمول:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .\config.example.env .\.env -Force
python -m flask db upgrade
python -m scripts.seed_demo_data
python -m flask run --host=0.0.0.0
```

متغیرهای محیطی موردنیاز backend، بدون مقدار:

- `FLASK_APP`
- `FLASK_ENV`
- `FLASK_DEBUG`
- `FLASK_RUN_PORT`
- `SECRET_KEY`
- `JWT_SECRET_KEY` یا alias `JWT_SECRET`
- `DATABASE_URL`
- `CORS_ALLOWED_ORIGINS`
- `BCRYPT_LOG_ROUNDS`
- `MAX_CONTENT_LENGTH`
- `LOG_LEVEL`
- `LOG_FORMAT`
- `LOG_DATEFMT`

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

نکته Windows/PowerShell: در محیط بررسی، اجرای `npm` از PowerShell به خاطر execution policy مسدود شد. استفاده از `npm.cmd` کار کرد:

```powershell
npm.cmd run lint
npm.cmd run build
```

متغیرهای frontend:

- `VITE_API_BASE_URL`
- `VITE_API_TIMEOUT_MS`

### KPI microservice

```powershell
cd <project-root>
python -m venv .venv
.\.venv\Scripts\pip install -r api\requirements.txt
$env:FLASK_APP="api/app.py"
python -m flask run --port 5001
```

متغیرهای موردنیاز:

- `KPI_API_KEY`
- `PGHOST`
- `PGPORT`
- `PGUSER`
- `PGPASSWORD`
- `PGDATABASE`

### تست و build

Backend:

```powershell
cd backend
python -m pytest
```

Frontend:

```powershell
cd frontend
npm.cmd run lint
npm.cmd run build
```

---

## 9. وضعیت تست و کیفیت

### تست‌ها

Backend:

- `backend/tests/test_auth_security.py`: login، failure، RBAC admin upload، تغییر role.
- `backend/tests/test_invoice_access.py`: scope پیمانکار و دسترسی staff.
- `backend/tests/test_jwt_invalid.py`: رد JWT نامعتبر بدون دیتابیس واقعی.
- چند فایل test/script قدیمی‌تر در `backend/` ریشه نیز وجود دارد که زیر `pytest.ini` فعلی اجرا نمی‌شوند.

Frontend:

- تست واحد/کامپوننت برای frontend دیده نشد.
- فقط lint و build تعریف شده‌اند.

### نتیجه اجرای واقعی در محیط بررسی

- `python -m pytest` در اجرای اول fail شد چون مقدار محیطی `LOG_FORMAT` با `logging.Formatter` سازگار نبود.
- با override کردن `LOG_FORMAT` به فرمت معتبر، نتیجه: `1 passed, 8 skipped`. تست‌های integration به دلیل نبود `TEST_DATABASE_URL` skip شدند.
- `npm.cmd run lint` fail شد با 10 خطای ESLint، عمدتاً unused variable و یک rule مربوط به Fast Refresh.
- `npm.cmd run build` موفق شد.

### کیفیت کد و مشکلات محتمل

- duplication زیاد در رنگ‌بندی status بین `DashboardPage`, `InvoicesTable`, `InvoiceDetailPage`.
- console logهای متعدد در production bundle احتمالاً باقی می‌مانند.
- بعضی docs با طراحی مطلوب فاصله دارند؛ مثال: ops-security پیشنهاد Argon2id و password تصادفی داده، اما کد فعلی bcrypt و password مشتق از کد پیمانکار دارد.
- `FiltersBar` prop `onReset` را می‌گیرد ولی استفاده نمی‌کند.
- `AdminUploadPage` بسیار بزرگ است و چند مسئولیت را همزمان دارد.
- importها داده قبلی را حذف و commit می‌کنند؛ ریسک از دست رفتن داده در شکست میانی.
- فایل‌ها/اسکریپت‌های قدیمی در `scripts/` و `db/sql/` با app جدید هم‌پوشانی دارند و وضعیت مرجع بودنشان نیازمند بررسی بیشتر است.

---

## 10. امنیت و پایداری

### Secretها و مقدارهای حساس

محل‌هایی که متغیر یا نمونه حساس دارند:

- `backend/config.example.env`: نام متغیرهای `SECRET_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL`, `KPI_API_KEY`, `PGPASSWORD`.
- `api/README.md`: نمونه تنظیمات DB شامل password دیده شد؛ مقدار در این گزارش redacted است.
- `db/README.md`: نمونه تنظیمات DB شامل password دیده شد؛ مقدار در این گزارش redacted است.
- `scripts/load_*.py`: fallback/default برای `PGPASSWORD` دیده شد؛ مقدار در این گزارش redacted است.
- `README.md` و `RUN_GUIDE_FA.md`: credentialهای demo ذکر شده‌اند؛ مقدار در این گزارش redacted است.

جمع‌بندی: secret اصلی backend در کد app به‌صورت fail-fast محافظت شده، اما مستندات و اسکریپت‌های کمکی نیازمند پاکسازی مقدارهای نمونه حساس هستند.

### CORS

- backend اصلی `CORS_ALLOWED_ORIGINS` را اجباری می‌خواهد.
- origin فقط اگر در لیست env باشد allow می‌شود.
- `supports_credentials=False` است.
- error handler هم CORS headers را برای origin مجاز تنظیم می‌کند.

### Password hashing

- رمزها با bcrypt hash می‌شوند.
- `BCRYPT_LOG_ROUNDS` validate می‌شود.
- اما تولید password پیمانکار از کدهای قابل حدس انجام می‌شود و `must_change_password=False` است؛ این برای production ریسک زیاد دارد.

### حفاظت endpointهای admin

- backend با `@require_staff` محافظت می‌کند.
- frontend هم صفحه admin را برای غیر staff redirect می‌کند، ولی حفاظت اصلی درست در backend است.

### لاگ‌ها

- audit log طراحی شده که password/token/filename ثبت نکند.
- backend exceptionها را با `error_id` ثبت می‌کند.
- frontend console logهای متعدد ممکن است داده‌های response و جزئیات فاکتور را در browser console نشان دهند.
- مقدار نامعتبر `LOG_FORMAT=json` باعث fail شدن app/test شد؛ validate فرمت logging یا پشتیبانی واقعی JSON logging پیشنهاد می‌شود.

### امکان مشاهده اطلاعات پیمانکار دیگر

- تست برای جلوگیری از مشاهده invoice پیمانکار دیگر وجود دارد، اما فقط با `TEST_DATABASE_URL` اجرا می‌شود و در محیط فعلی skip شد.
- در کد scope اصلی روی `detail_code` و `supplier_code` است.
- fallback cover-based نیازمند تست بیشتر با داده واقعی است.

### خرابی داده در import

- importها atomic نیستند.
- حذف داده قبلی قبل از تکمیل پردازش، همراه با commitهای میانی، می‌تواند در شکست، داده قبلی را از بین ببرد.
- rollback فقط transaction فعلی را برمی‌گرداند، نه dataset حذف‌شده و commit‌شده قبلی.

---

## 11. نقاط مبهم و ریسک‌های فعلی

| ریسک | محل مشاهده در کد | شدت | توضیح | پیشنهاد اصلاح |
|---|---|---:|---|---|
| import غیر atomic و حذف داده قبلی | `backend/app/services/contractors_one_importer.py`, `contractors_two_importer.py`, `codtafsiltamin_importer.py` | زیاد | داده قبلی delete و commit می‌شود؛ شکست بعدی rollback کامل ندارد. | staging table، validation کامل قبل از swap، transaction واحد یا versioned import با فعال‌سازی batch موفق |
| ناسازگاری `Contractor(last_update_batch_id=...)` | `backend/app/services/codtafsiltamin_importer.py` و `backend/app/models/__init__.py` | زیاد | مدل `Contractor` چنین فیلدی ندارد؛ import پیمانکار ممکن است با keyword نامعتبر fail شود. | یا ستون/migration اضافه شود یا پارامتر حذف شود؛ تست import اضافه شود |
| password پیمانکار قابل حدس | `backend/app/utils/auth_utils.py`, `backend/app/routes/admin.py` | زیاد | password از کد تفصیلی/تامین‌کننده ساخته می‌شود و تغییر رمز پیمانکار غیرفعال است. | password تصادفی، reset اجباری، کانال تحویل امن، rate limiting |
| مقادیر حساس نمونه در docs/scripts | `api/README.md`, `db/README.md`, `scripts/load_*.py`, READMEها | زیاد | password/credential نمونه در repository دیده می‌شود. | حذف مقدار واقعی/نمونه حساس، استفاده از placeholder امن، secret scanning |
| refresh token در localStorage | `frontend/src/api/authStorage.js` | متوسط/زیاد | در XSS قابل سرقت است. | cookie امن HttpOnly یا token rotation و CSP سخت‌تر |
| skip شدن تست‌های اصلی بدون DB | `backend/tests/conftest.py` | متوسط | فقط 1 تست بدون DB اجرا شد؛ RBAC/invoice access در محیط فعلی اجرا نشد. | test DB استاندارد، Docker/compose یا fixture transaction |
| lint فرانت fail | `frontend/src/*` | متوسط | 10 خطای ESLint، از جمله unused و Fast Refresh. | پاکسازی unusedها و جداکردن exportهای provider |
| console log داده‌ها | `frontend/src/pages/*`, `ProtectedRoute.jsx` | متوسط | داده‌های فاکتور/progress ممکن است در console بماند. | حذف یا gate کردن logها با dev flag |
| fallback دسترسی invoice از طریق cover/detail | `backend/app/routes/invoices.py` | متوسط | برای داده ناقص طراحی شده اما ممکن است scope را پیچیده کند. | تست ماتریسی با supplier_code null/empty و cover مشترک |
| endpoint `/admin/uploads` placeholder | `backend/app/routes/admin.py` | کم/متوسط | مسیر عمومی admin upload فقط batch placeholder می‌سازد و ingest نمی‌کند. | حذف یا مستندسازی دقیق کاربرد |
| microservice KPI جدا از auth اصلی | `api/app.py` | متوسط | API key مستقل، policy جدا و connection جدا دارد. | یکپارچه‌سازی auth/observability یا مستندسازی deployment مستقل |
| مستندات امنیتی با کد فعلی ناهماهنگ | `docs/ops-security.md` در برابر کد auth | متوسط | docs از Argon2id و password تصادفی می‌گوید، کد bcrypt و password مشتق دارد. | sync docs با واقعیت یا اجرای برنامه امنیتی docs |

---

## 12. پیشنهاد نقشه راه کوتاه

### فاز ۱: تثبیت و امنیت

- پاکسازی مقدارهای حساس از docs/scripts و جایگزینی با placeholder امن.
- اصلاح bug احتمالی `last_update_batch_id` در import پیمانکار.
- اجرای test DB پایدار و اجباری کردن تست‌های RBAC/invoice scope.
- حذف console logهای غیرضروری از frontend.
- افزودن rate limiting برای login.
- بازنگری تولید password پیمانکار و فعال‌سازی reset/change-password امن.
- validate یا اصلاح پشتیبانی `LOG_FORMAT` برای جلوگیری از fail شدن startup.

### فاز ۲: بهبود تجربه کاربری پیمانکار

- استانداردسازی نمایش وضعیت‌ها و رنگ‌ها در یک helper/component مشترک.
- بهبود پیام‌های خطای فارسی و یکسان‌سازی encoding/متن‌ها.
- تکمیل empty stateها و loading stateهای جزئی.
- افزودن امکان دانلود/چاپ خلاصه وضعیت فاکتور در صورت نیاز کسب‌وکار.

### فاز ۳: بهبود import/reporting

- تبدیل import به فرآیند staging + validation + publish.
- امکان rollback به batch قبلی.
- گزارش دقیق خطاهای header و row با template قابل دانلود.
- ثبت history کامل batchها به جای حذف batchهای قبلی.
- مستندسازی رسمی ستون‌ها، enum وضعیت‌ها و mappingها.
- یکپارچه کردن یا مستندسازی جداگانه KPI microservice.

### فاز ۴: آماده‌سازی بهره‌برداری

- Docker/compose یا دستورالعمل deployment کامل.
- health check backend/frontend/KPI.
- backup و restore دیتابیس.
- لاگ ساختاریافته امن و monitoring.
- تنظیم CORS production، HTTPS و CSP مناسب frontend.
- CI برای backend tests، frontend lint و build.
- secret management بیرون از repository.

---

## 13. خلاصه قابل انتقال به ChatGPT

این پروژه یک وب‌اپ اطلاع‌رسانی وضعیت فاکتورها/صورتحساب‌های پیمانکاران است. پیمانکار بعد از ورود فقط فاکتورهای خودش را می‌بیند و staff/admin امکان مشاهده سراسری، import فایل Excel، پیگیری progress و بررسی خطاهای import را دارد.

Stack فنی: backend اصلی Flask/Python با SQLAlchemy، Flask-Migrate، Flask-JWT-Extended، Flask-Bcrypt، Flask-CORS، PostgreSQL، pandas/openpyxl و convertdate است. frontend با React 19، Vite، MUI، React Router، TanStack Query و Axios نوشته شده است. پوشه `api/` یک Flask microservice جدا برای KPI و export CSV/XLSX با API key و psycopg2 دارد.

مدل‌های اصلی: `Contractor`, `User`, `InvoiceSummary`, `InvoiceDetail`, `ImportBatch`, `ImportError`, `AuditLog`. ارتباط‌ها عمدتاً با `contractor_id`, `last_update_batch_id`, `batch_id` و `user_id` هستند؛ summary و detail از طریق `cover_number` نیز مرتبط می‌شوند.

APIهای اصلی: `/auth/login`, `/auth/refresh`, `/auth/me`, `/auth/change-password`, `/invoices/`, `/invoices/<cover_number>`, `/invoices/filters/options`, `/admin/uploads/*`, `/admin/templates/*`, `/admin/contractors`, `/admin/contractors/<id>/create-user`, `/admin/invoice-summaries`, `/admin/invoice-details`. KPI جداگانه شامل `/api/kpi/yearly` و `/api/kpi/yearly/export` است.

صفحات اصلی frontend: `/`, `/login`, `/invoices`, `/invoice/:coverNumber`, `/admin/uploads`. پیمانکار dashboard فاکتورها، فیلتر سال/وضعیت/جستجو و جزئیات روکش را می‌بیند. staff/admin علاوه بر dashboard، صفحه upload و مرور داده‌های import شده را دارد.

وضعیت فعلی: پروژه functional و در حال توسعه است، اما برای بهره‌برداری نیازمند تثبیت است. build فرانت موفق شد، lint فرانت با 10 خطا fail شد. backend pytest بدون DB واقعی فقط 1 تست را اجرا کرد و 8 تست integration skip شدند؛ اجرای اولیه pytest به دلیل `LOG_FORMAT` نامعتبر fail شد.

مهم‌ترین ریسک‌ها: importها atomic نیستند و داده قبلی را قبل از تکمیل import حذف/commit می‌کنند؛ importer پیمانکار احتمالاً پارامتر `last_update_batch_id` را به مدلی می‌دهد که چنین ستون ندارد؛ password پیمانکار از کدهای قابل حدس تولید می‌شود؛ refresh token در localStorage ذخیره می‌شود؛ مقدارهای نمونه حساس در docs/scripts دیده می‌شوند؛ تست‌های اصلی بدون دیتابیس اجرا نمی‌شوند.

پیشنهاد قدم بعدی: ابتدا فاز تثبیت امنیتی انجام شود: پاکسازی secretهای نمونه، اصلاح importer پیمانکار، ساخت test DB قابل تکرار، اجرای کامل تست‌های RBAC/scope، حذف console logهای حساس، و بازطراحی import به staging + publish با rollback یا versioning.
