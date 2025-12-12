-- Compact KPI view selecting essential fields only

CREATE OR REPLACE VIEW public.v_kpi_yearly_compact AS
SELECT
	source,
	customer_uid,
	supplier_name,
	year_j,
	status,
	count,
	amount_a,
	amount_b
FROM public.v_supplier_kpi_yearly;






