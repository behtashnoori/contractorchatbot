-- Core schema for codtafsiltamin in core_db

CREATE SCHEMA IF NOT EXISTS public;

CREATE TABLE IF NOT EXISTS public.dim_supplier_account (
	id                BIGSERIAL PRIMARY KEY,
	supplier_code     TEXT NOT NULL,
	tafsili_code      TEXT NOT NULL,
	customer_uid      TEXT GENERATED ALWAYS AS (supplier_code || '-' || tafsili_code) STORED,
	supplier_name     TEXT,
	status            TEXT,
	type              TEXT,
	start_date        DATE,           -- Gregorian; optional
	start_date_jalali TEXT,           -- raw original text
	created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
	updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
	UNIQUE (supplier_code, tafsili_code),
	UNIQUE (customer_uid)
);

CREATE INDEX IF NOT EXISTS idx_dim_supplier_account_supplier_code ON public.dim_supplier_account (supplier_code);
CREATE INDEX IF NOT EXISTS idx_dim_supplier_account_tafsili_code ON public.dim_supplier_account (tafsili_code);

-- Persian text normalization helper (immutable) for matching supplier names
CREATE OR REPLACE FUNCTION public.normalize_persian(s TEXT)
RETURNS TEXT
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
AS $$
	SELECT
		trim(
			regexp_replace(
				regexp_replace(
					translate(coalesce(s, ''),
						'يك‌\u200c()[]{}،,._-"''–—-',
						'یک                          '  -- map Arabic Yeh/Kaf to Persian; drop ZWNJ/punct to spaces
					),
					'\s+', ' ', 'g'           -- collapse spaces
				),
				'^\s+|\s+$', '', 'g'         -- trim just in case
			)
		);
$$;

-- Optional for similarity suggestions
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Normalized name column for faster joins
ALTER TABLE IF EXISTS public.dim_supplier_account
	ADD COLUMN IF NOT EXISTS supplier_name_norm TEXT GENERATED ALWAYS AS (public.normalize_persian(supplier_name)) STORED;

CREATE INDEX IF NOT EXISTS idx_dim_supplier_account_name_norm ON public.dim_supplier_account (supplier_name_norm);

-- Alias table for supplier names to customer_uid
CREATE TABLE IF NOT EXISTS public.supplier_aliases (
	alias_id       BIGSERIAL PRIMARY KEY,
	alias_name     TEXT NOT NULL,
	alias_norm     TEXT GENERATED ALWAYS AS (public.normalize_persian(alias_name)) STORED,
	customer_uid   TEXT NOT NULL REFERENCES public.dim_supplier_account(customer_uid),
	source_note    TEXT,
	created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
	UNIQUE (alias_norm)
);

CREATE INDEX IF NOT EXISTS idx_supplier_aliases_norm ON public.supplier_aliases (alias_norm);

-- Fact table for invoices (file 2)
CREATE TABLE IF NOT EXISTS public.fact_invoices (
	invoice_id         BIGSERIAL PRIMARY KEY,
	customer_uid       TEXT,            -- resolved if supplier_name matches a known account
	supplier_name_raw  TEXT NOT NULL,
	request_no         TEXT,
	beneficiary        TEXT,
	department         TEXT,
	status             TEXT,
	invoice_cost_type  TEXT,
	amount_wo_tax      NUMERIC(20,2),
	total_amount       NUMERIC(20,2),
	created_at_jalali  TEXT,
	delivered_to_acc_j TEXT,
	in_observer_j      TEXT,
	loaded_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fact_invoices_customer_uid ON public.fact_invoices (customer_uid);
CREATE INDEX IF NOT EXISTS idx_fact_invoices_supplier_name_raw ON public.fact_invoices (supplier_name_raw);

-- Add cover_no generated column to invoices for joining to covers
ALTER TABLE IF EXISTS public.fact_invoices
	ADD COLUMN IF NOT EXISTS cover_no TEXT GENERATED ALWAYS AS (request_no) STORED;
CREATE INDEX IF NOT EXISTS idx_fact_invoices_cover_no ON public.fact_invoices (cover_no);

-- Cover dimension (file 1)
CREATE TABLE IF NOT EXISTS public.dim_cover (
	cover_id          BIGSERIAL PRIMARY KEY,
	cover_no          TEXT NOT NULL UNIQUE,
	customer_uid      TEXT,             -- resolved via supplier name normalization
	supplier_name_raw TEXT,
	cover_date_jalali TEXT,
	unit_or_code      TEXT,
	status            TEXT,
	description       TEXT,
	created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
	updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_dim_cover_cover_no ON public.dim_cover (cover_no);
CREATE INDEX IF NOT EXISTS idx_dim_cover_customer_uid ON public.dim_cover (customer_uid);

-- Fact for contractors-2 file
CREATE TABLE IF NOT EXISTS public.fact_contractors2 (
	row_id            BIGSERIAL PRIMARY KEY,
	customer_uid      TEXT,            -- resolved via aliases or normalized name
	supplier_name_raw TEXT NOT NULL,
	doc_no            TEXT,
	doc_date_jalali   TEXT,
	unit_or_code      TEXT,
	status            TEXT,
	item_title        TEXT,
	gross_amount      NUMERIC(20,2),
	basis             TEXT,
	description       TEXT,
	loaded_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fact_contractors2_customer_uid ON public.fact_contractors2 (customer_uid);
CREATE INDEX IF NOT EXISTS idx_fact_contractors2_supplier_raw ON public.fact_contractors2 (supplier_name_raw);


