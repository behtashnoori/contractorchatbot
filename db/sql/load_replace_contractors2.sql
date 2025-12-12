-- Replace-load for contractors-2 (file 3)
-- 1) TRUNCATE previous data (landing + fact)
-- 2) Run Python loader to insert fresh rows into landing
-- 3) Rebuild fact via upsert

BEGIN;
TRUNCATE TABLE landing.contractors2_stage;
TRUNCATE TABLE public.fact_contractors2;
COMMIT;

-- After running the loader:
-- \i db/sql/upsert_contractors2.sql






