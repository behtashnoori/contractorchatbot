-- Cover-level KPI and join to invoices

CREATE OR REPLACE VIEW public.v_covers_kpi AS
SELECT
	dc.cover_no,
	dc.customer_uid,
	coalesce(dsa.supplier_name, dc.supplier_name_raw) AS supplier_name,
	substring(dc.cover_date_jalali FROM 1 FOR 4)      AS year_j,
	dc.status                                         AS cover_status,
	COUNT(fi.invoice_id)                              AS invoice_count,
	SUM(coalesce(fi.total_amount, 0))                 AS total_amount_sum
FROM public.dim_cover dc
LEFT JOIN public.dim_supplier_account dsa
	ON dsa.customer_uid = dc.customer_uid
LEFT JOIN public.fact_invoices fi
	ON fi.cover_no = dc.cover_no
GROUP BY 1,2,3,4,5;

-- Drill-down view: each invoice row under its cover
CREATE OR REPLACE VIEW public.v_cover_invoices AS
SELECT
	dc.cover_no,
	dc.customer_uid,
	coalesce(dsa.supplier_name, dc.supplier_name_raw) AS supplier_name,
	fi.invoice_id,
	fi.status AS invoice_status,
	fi.total_amount,
	fi.amount_wo_tax,
	fi.created_at_jalali
FROM public.dim_cover dc
LEFT JOIN public.dim_supplier_account dsa
	ON dsa.customer_uid = dc.customer_uid
JOIN public.fact_invoices fi
	ON fi.cover_no = dc.cover_no;






