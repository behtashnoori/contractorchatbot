-- KPI Views per supplier/year/status (Jalali year derived from first 4 chars)

CREATE OR REPLACE VIEW public.v_invoices_kpi_yearly AS
SELECT
	dsa.customer_uid,
	coalesce(dsa.supplier_name, fi.supplier_name_raw) AS supplier_name,
	substring(fi.created_at_jalali FROM 1 FOR 4)       AS year_j,
	coalesce(fi.status, 'نامشخص')                      AS status,
	COUNT(*)                                           AS invoice_count,
	SUM(coalesce(fi.amount_wo_tax, 0))                 AS amount_wo_tax_sum,
	SUM(coalesce(fi.total_amount, 0))                  AS total_amount_sum
FROM public.fact_invoices fi
LEFT JOIN public.dim_supplier_account dsa
	ON dsa.customer_uid = fi.customer_uid
GROUP BY 1,2,3,4;

CREATE OR REPLACE VIEW public.v_contractors2_kpi_yearly AS
SELECT
	dsa.customer_uid,
	coalesce(dsa.supplier_name, fc2.supplier_name_raw) AS supplier_name,
	substring(fc2.doc_date_jalali FROM 1 FOR 4)        AS year_j,
	coalesce(fc2.status, 'نامشخص')                     AS status,
	COUNT(*)                                           AS row_count,
	SUM(coalesce(fc2.gross_amount, 0))                 AS gross_amount_sum
FROM public.fact_contractors2 fc2
LEFT JOIN public.dim_supplier_account dsa
	ON dsa.customer_uid = fc2.customer_uid
GROUP BY 1,2,3,4;

-- Unified tidy view with a source column
CREATE OR REPLACE VIEW public.v_supplier_kpi_yearly AS
SELECT
	'invoices'::text AS source,
	customer_uid,
	supplier_name,
	year_j,
	status,
	invoice_count        AS count,
	amount_wo_tax_sum    AS amount_a,
	total_amount_sum     AS amount_b
FROM public.v_invoices_kpi_yearly
UNION ALL
SELECT
	'contractors2'::text,
	customer_uid,
	supplier_name,
	year_j,
	status,
	row_count,
	gross_amount_sum,
	NULL::numeric
FROM public.v_contractors2_kpi_yearly;






