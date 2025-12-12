-- Upsert covers (file 1) from landing.covers_stage into public.dim_cover
-- Resolve customer_uid via aliases/normalized supplier name

WITH src AS (
	SELECT
		TRIM(s.cover_no)           AS cover_no,
		TRIM(s.supplier_name)      AS supplier_name_raw,
		s.cover_date_jalali,
		s.unit_or_code,
		s.status,
		s.description
	FROM landing.covers_stage s
	WHERE s.cover_no IS NOT NULL
),
resolved AS (
	SELECT
		src.*,
		COALESCE(sa.customer_uid, dsa.customer_uid) AS customer_uid
	FROM src
	LEFT JOIN public.supplier_aliases sa
		ON public.normalize_persian(src.supplier_name_raw) = sa.alias_norm
	LEFT JOIN public.dim_supplier_account dsa
		ON public.normalize_persian(src.supplier_name_raw) = dsa.supplier_name_norm
)
INSERT INTO public.dim_cover (
	cover_no,
	customer_uid,
	supplier_name_raw,
	cover_date_jalali,
	unit_or_code,
	status,
	description
)
SELECT
	cover_no,
	customer_uid,
	supplier_name_raw,
	cover_date_jalali,
	unit_or_code,
	status,
	description
FROM resolved
ON CONFLICT (cover_no) DO UPDATE
SET customer_uid      = EXCLUDED.customer_uid,
	supplier_name_raw = EXCLUDED.supplier_name_raw,
	cover_date_jalali = EXCLUDED.cover_date_jalali,
	unit_or_code      = EXCLUDED.unit_or_code,
	status            = EXCLUDED.status,
	description       = EXCLUDED.description,
	updated_at        = now();






