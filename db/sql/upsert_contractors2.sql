-- Upsert contractors-2 file from landing.contractors2_stage into public.fact_contractors2
-- Resolution order: supplier_aliases by normalized name, then direct normalized match

WITH src AS (
	SELECT
		TRIM(s.supplier_name) AS supplier_name_raw,
		s.doc_no,
		s.doc_date_jalali,
		s.unit_or_code,
		s.status,
		s.item_title,
		s.gross_amount,
		s.basis,
		s.description
	FROM landing.contractors2_stage s
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
INSERT INTO public.fact_contractors2 (
	customer_uid,
	supplier_name_raw,
	doc_no,
	doc_date_jalali,
	unit_or_code,
	status,
	item_title,
	gross_amount,
	basis,
	description
)
SELECT
	customer_uid,
	supplier_name_raw,
	doc_no,
	doc_date_jalali,
	unit_or_code,
	status,
	item_title,
	gross_amount,
	basis,
	description
FROM resolved;






