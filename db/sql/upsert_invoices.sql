-- Upsert file 2 (invoices) using strong name resolution:
-- 1) Try alias table match by normalized name
-- 2) Else try direct match to dim_supplier_account by normalized name

WITH src AS (
	SELECT
		TRIM(s.supplier_name)                   AS supplier_name_raw,
		s.request_no,
		s.beneficiary,
		s.department,
		s.status,
		s.invoice_cost_type,
		s.amount_wo_tax,
		s.total_amount,
		s.created_at_jalali,
		s.delivered_to_acc_j,
		s.in_observer_j
	FROM landing.invoices_stage s
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
INSERT INTO public.fact_invoices (
	customer_uid,
	supplier_name_raw,
	request_no,
	beneficiary,
	department,
	status,
	invoice_cost_type,
	amount_wo_tax,
	total_amount,
	created_at_jalali,
	delivered_to_acc_j,
	in_observer_j
)
SELECT
	customer_uid,
	supplier_name_raw,
	request_no,
	beneficiary,
	department,
	status,
	invoice_cost_type,
	amount_wo_tax,
	total_amount,
	created_at_jalali,
	delivered_to_acc_j,
	in_observer_j
FROM resolved;


