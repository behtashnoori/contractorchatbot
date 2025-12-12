-- Replace-load for codtafsiltamin (file 1)
-- Steps:
-- 1) Run this TRUNCATE to clear previous data.
-- 2) Execute the Python loader to insert the fresh file into landing.
-- 3) Run the upsert to rebuild the dim table.

BEGIN;
TRUNCATE TABLE landing.codtafsiltamin_stage;
TRUNCATE TABLE public.dim_supplier_account;
COMMIT;

-- After running the loader:
-- \i db/sql/upsert_codtafsiltamin.sql






