-- Staging schema for codtafsiltamin
-- Database: staging_db (create separately if needed)

CREATE SCHEMA IF NOT EXISTS landing;

CREATE TABLE IF NOT EXISTS landing.codtafsiltamin_stage (
	stage_id           BIGSERIAL PRIMARY KEY,
	batch_id           UUID NOT NULL,
	source_filename    TEXT NOT NULL,
	ingested_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

	-- raw columns mapped from file
	supplier_code      TEXT,            -- کد تامین کننده
	supplier_name      TEXT,            -- نام تامین کننده
	status             TEXT,            -- وضعیت
	type               TEXT,            -- نوع
	start_date_jalali  TEXT,            -- تاریخ شروع ارتباط (جلالی، مثال: 1404/02/08)
	tafsili_code       TEXT             -- کد تفصیلی
);

CREATE INDEX IF NOT EXISTS idx_codtafsiltamin_stage_supplier_code ON landing.codtafsiltamin_stage (supplier_code);
CREATE INDEX IF NOT EXISTS idx_codtafsiltamin_stage_tafsili_code ON landing.codtafsiltamin_stage (tafsili_code);

-- File 2: Invoices/requests (generic columns based on shared screenshot)
CREATE TABLE IF NOT EXISTS landing.invoices_stage (
	stage_id           BIGSERIAL PRIMARY KEY,
	batch_id           UUID NOT NULL,
	source_filename    TEXT NOT NULL,
	ingested_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

	-- raw columns
	supplier_name      TEXT,            -- تامین کننده
	request_no         TEXT,            -- شماره روکش/شماره درخواست
	beneficiary        TEXT,            -- بهره بردار
	department         TEXT,            -- واحد/حوزه
	status             TEXT,            -- وضعیت فاکتور/تأیید
	invoice_cost_type  TEXT,            -- نوع هزینه فاکتور
	amount_wo_tax      NUMERIC(20,2),   -- مبلغ بدون مالیات بر ارزش افزوده
	total_amount       NUMERIC(20,2),   -- مبلغ کل
	created_at_jalali  TEXT,            -- تاریخ ایجاد فاکتور
	delivered_to_acc_j TEXT,            -- تاریخ تحویل به حسابداری
	in_observer_j      TEXT,            -- در اختیار ناظر (تاریخ)
	other_cols_json    JSONB            -- نگهداری سایر ستون‌های احتمالی
);

CREATE INDEX IF NOT EXISTS idx_invoices_stage_supplier_name ON landing.invoices_stage (supplier_name);

-- File 3: contractors-2 (purchase items summary)
CREATE TABLE IF NOT EXISTS landing.contractors2_stage (
	stage_id           BIGSERIAL PRIMARY KEY,
	batch_id           UUID NOT NULL,
	source_filename    TEXT NOT NULL,
	ingested_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

	-- raw columns mapped from screenshot
	doc_no             TEXT,            -- شماره
	doc_date_jalali    TEXT,            -- تاریخ
	unit_or_code       TEXT,            -- واحد/رمز تامین
	supplier_name      TEXT,            -- تامین کننده
	status             TEXT,            -- وضعیت
	item_title         TEXT,            -- عنوان قلم خرید
	gross_amount       NUMERIC(20,2),   -- مبلغ ناخالص
	basis              TEXT,            -- مبنا
	description        TEXT             -- توضیحات
);

CREATE INDEX IF NOT EXISTS idx_contractors2_stage_supplier_name ON landing.contractors2_stage (supplier_name);

-- File 1 (covers): rockesh master
CREATE TABLE IF NOT EXISTS landing.covers_stage (
	stage_id           BIGSERIAL PRIMARY KEY,
	batch_id           UUID NOT NULL,
	source_filename    TEXT NOT NULL,
	ingested_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

	cover_no           TEXT,            -- شماره روکش
	cover_date_jalali  TEXT,            -- تاریخ
	unit_or_code       TEXT,            -- واحد/رمز تامین (در صورت وجود)
	supplier_name      TEXT,            -- نام تامین کننده
	status             TEXT,            -- وضعیت روکش
	description        TEXT             -- توضیحات/سایر
);

CREATE INDEX IF NOT EXISTS idx_covers_stage_cover_no ON landing.covers_stage (cover_no);
CREATE INDEX IF NOT EXISTS idx_covers_stage_supplier_name ON landing.covers_stage (supplier_name);


