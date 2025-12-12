-- Data quality and simple reporting for codtafsiltamin

-- 1) Missing composite keys in staging
SELECT *
FROM landing.codtafsiltamin_stage
WHERE supplier_code IS NULL OR tafsili_code IS NULL;

-- 2) Duplicates in staging by (supplier_code, tafsili_code, start_date_jalali)
SELECT
	TRIM(supplier_code) AS supplier_code,
	TRIM(tafsili_code)  AS tafsili_code,
	TRIM(start_date_jalali) AS start_date_jalali,
	COUNT(*) AS cnt
FROM landing.codtafsiltamin_stage
GROUP BY 1,2,3
HAVING COUNT(*) > 1
ORDER BY cnt DESC;

-- 3) Coverage in core
SELECT COUNT(*) AS total_accounts FROM public.dim_supplier_account;

-- 4) Active by supplier (if status uses 'فعال')
SELECT supplier_code, COUNT(*) AS active_count
FROM public.dim_supplier_account
WHERE status = 'فعال'
GROUP BY supplier_code
ORDER BY active_count DESC;


