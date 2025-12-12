-- Replace-load for invoices (file 2)
-- 1) TRUNCATE previous data (landing + fact)
-- 2) Run Python loader to insert fresh rows into landing
-- 3) Rebuild fact via upsert

BEGIN;
TRUNCATE TABLE landing.invoices_stage;
TRUNCATE TABLE public.fact_invoices;
COMMIT;

-- After running the loader:
-- \i db/sql/upsert_invoices.sql






