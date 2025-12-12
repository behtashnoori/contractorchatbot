-- Upsert from landing.codtafsiltamin_stage to public.dim_supplier_account
-- Assumes both schemas (landing, public) are in the same database (contractor_portal).

-- Without Jalali conversion (store raw jalali text; optional Gregorian left NULL)
INSERT INTO public.dim_supplier_account (
	supplier_code,
	tafsili_code,
	supplier_name,
	status,
	type,
	start_date_jalali
)
SELECT
	TRIM(s.supplier_code),
	TRIM(s.tafsili_code),
	NULLIF(TRIM(s.supplier_name), ''),
	NULLIF(TRIM(s.status), ''),
	NULLIF(TRIM(s.type), ''),
	NULLIF(TRIM(s.start_date_jalali), '')
FROM landing.codtafsiltamin_stage s
WHERE s.supplier_code IS NOT NULL AND s.tafsili_code IS NOT NULL
ON CONFLICT (supplier_code, tafsili_code) DO UPDATE
SET supplier_name     = EXCLUDED.supplier_name,
	status            = EXCLUDED.status,
	type              = EXCLUDED.type,
	start_date_jalali = COALESCE(EXCLUDED.start_date_jalali, public.dim_supplier_account.start_date_jalali),
	updated_at        = now();


