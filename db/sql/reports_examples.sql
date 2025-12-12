-- Example KPI queries

-- 1) Yearly/status KPI for a specific supplier by name (normalized match)
-- Set :supplier_name to the visible name
-- \set supplier_name 'نام تامین کننده'
SELECT *
FROM public.v_supplier_kpi_yearly
WHERE public.normalize_persian(supplier_name) = public.normalize_persian(:'supplier_name')
ORDER BY source, year_j, status;

-- 2) Yearly/status KPI for a specific customer_uid (faster)
-- \set uid '732-0026968'
SELECT *
FROM public.v_supplier_kpi_yearly
WHERE customer_uid = :'uid'
ORDER BY source, year_j, status;

-- 3) Pivot-style totals (invoices only) for one supplier_uid
-- \set uid '732-0026968'
SELECT
	year_j,
	SUM(CASE WHEN status='تایید شده' THEN count ELSE 0 END) AS cnt_approved,
	SUM(CASE WHEN status='ثبت شده'  THEN count ELSE 0 END) AS cnt_registered,
	SUM(CASE WHEN source='invoices' THEN amount_b ELSE 0 END) AS total_amount_sum
FROM public.v_supplier_kpi_yearly
WHERE customer_uid = :'uid'
GROUP BY year_j
ORDER BY year_j;






