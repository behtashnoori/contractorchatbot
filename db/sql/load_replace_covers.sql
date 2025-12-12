-- Replace-load for covers (file 1)
BEGIN;
TRUNCATE TABLE landing.covers_stage;
TRUNCATE TABLE public.dim_cover;
COMMIT;

-- After running the loader:
-- \i db/sql/upsert_covers.sql






