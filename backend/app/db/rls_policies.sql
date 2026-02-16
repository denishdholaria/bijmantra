-- VAJRA: RLS policy hardening and security-view pattern
-- Pattern: base table (RLS) -> sec_* view (security barrier + tenant filter) -> API/final views

BEGIN;

-- -----------------------------------------------------------------------------
-- Helpers
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION app_owner_or_admin(target_org_id integer)
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
    SELECT current_organization_id() = 0 OR current_organization_id() = target_org_id;
$$;

-- -----------------------------------------------------------------------------
-- Security-view pattern for biometrics domain
-- -----------------------------------------------------------------------------
-- Base tables are expected to own RLS policies.

DROP VIEW IF EXISTS sec_gs_models CASCADE;
CREATE VIEW sec_gs_models
WITH (security_barrier = true)
AS
SELECT *
FROM gs_models
WHERE app_owner_or_admin(organization_id);

DROP VIEW IF EXISTS sec_stability_results CASCADE;
CREATE VIEW sec_stability_results
WITH (security_barrier = true)
AS
SELECT *
FROM stability_results
WHERE app_owner_or_admin(organization_id);

DROP VIEW IF EXISTS sec_cross_predictions CASCADE;
CREATE VIEW sec_cross_predictions
WITH (security_barrier = true)
AS
SELECT *
FROM cross_predictions
WHERE app_owner_or_admin(organization_id);

-- Final views consume only sec_* views (prevents recursive RLS dependency chains).
DROP VIEW IF EXISTS v_biometrics_gs_models CASCADE;
CREATE VIEW v_biometrics_gs_models AS
SELECT * FROM sec_gs_models;

DROP VIEW IF EXISTS v_biometrics_stability_results CASCADE;
CREATE VIEW v_biometrics_stability_results AS
SELECT * FROM sec_stability_results;

DROP VIEW IF EXISTS v_biometrics_cross_predictions CASCADE;
CREATE VIEW v_biometrics_cross_predictions AS
SELECT * FROM sec_cross_predictions;

-- -----------------------------------------------------------------------------
-- Biometrics RLS policies
-- -----------------------------------------------------------------------------
ALTER TABLE IF EXISTS gs_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS gs_models FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS gs_models_tenant_isolation ON gs_models;
CREATE POLICY gs_models_tenant_isolation
ON gs_models
FOR ALL
USING (app_owner_or_admin(organization_id))
WITH CHECK (app_owner_or_admin(organization_id));

ALTER TABLE IF EXISTS stability_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS stability_results FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS stability_results_tenant_isolation ON stability_results;
CREATE POLICY stability_results_tenant_isolation
ON stability_results
FOR ALL
USING (app_owner_or_admin(organization_id))
WITH CHECK (app_owner_or_admin(organization_id));

ALTER TABLE IF EXISTS cross_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS cross_predictions FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS cross_predictions_tenant_isolation ON cross_predictions;
CREATE POLICY cross_predictions_tenant_isolation
ON cross_predictions
FOR ALL
USING (app_owner_or_admin(organization_id))
WITH CHECK (app_owner_or_admin(organization_id));

-- -----------------------------------------------------------------------------
-- Indexes to support tenant isolation and recency filters
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_gs_models_org_created_at
ON gs_models(organization_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_stability_results_org_created_at
ON stability_results(organization_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_cross_predictions_org_created_at
ON cross_predictions(organization_id, created_at DESC);

COMMIT;

-- -----------------------------------------------------------------------------
-- Audit query: recursive view dependencies (run manually)
-- -----------------------------------------------------------------------------
-- WITH RECURSIVE view_graph AS (
--   SELECT
--     v.oid AS root_oid,
--     v.oid AS current_oid,
--     ARRAY[v.oid] AS visited,
--     0 AS depth
--   FROM pg_class v
--   JOIN pg_namespace n ON n.oid = v.relnamespace
--   WHERE v.relkind = 'v' AND n.nspname = 'public'
--
--   UNION ALL
--
--   SELECT
--     vg.root_oid,
--     d.refobjid AS current_oid,
--     vg.visited || d.refobjid,
--     vg.depth + 1
--   FROM view_graph vg
--   JOIN pg_depend d ON d.objid = vg.current_oid
--   JOIN pg_rewrite r ON r.oid = d.objid
--   JOIN pg_class c ON c.oid = r.ev_class
--   WHERE d.classid = 'pg_rewrite'::regclass
--     AND d.refclassid = 'pg_class'::regclass
--     AND d.refobjid = ANY(vg.visited) = false
-- )
-- SELECT DISTINCT root.relname AS root_view
-- FROM view_graph vg
-- JOIN pg_class root ON root.oid = vg.root_oid
-- WHERE vg.current_oid = ANY(vg.visited[1:array_length(vg.visited, 1)-1]);
