"""VAJRA RLS hardening and performance indexes

Revision ID: 051_vajra_rls_perf
Revises: ee15a10584c9
Create Date: 2026-02-15
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "051_vajra_rls_perf"
down_revision = "ee15a10584c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # RLS policies for biometrics family tables + simplified owner check helper.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_owner_or_admin(target_org_id integer)
        RETURNS boolean
        LANGUAGE sql
        STABLE
        AS $$
            SELECT current_organization_id() = 0 OR current_organization_id() = target_org_id;
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'gs_models') THEN
                ALTER TABLE gs_models ENABLE ROW LEVEL SECURITY;
                ALTER TABLE gs_models FORCE ROW LEVEL SECURITY;
                DROP POLICY IF EXISTS gs_models_tenant_isolation ON gs_models;
                CREATE POLICY gs_models_tenant_isolation ON gs_models
                    FOR ALL
                    USING (app_owner_or_admin(organization_id))
                    WITH CHECK (app_owner_or_admin(organization_id));
            END IF;

            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'stability_results') THEN
                ALTER TABLE stability_results ENABLE ROW LEVEL SECURITY;
                ALTER TABLE stability_results FORCE ROW LEVEL SECURITY;
                DROP POLICY IF EXISTS stability_results_tenant_isolation ON stability_results;
                CREATE POLICY stability_results_tenant_isolation ON stability_results
                    FOR ALL
                    USING (app_owner_or_admin(organization_id))
                    WITH CHECK (app_owner_or_admin(organization_id));
            END IF;

            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'cross_predictions') THEN
                ALTER TABLE cross_predictions ENABLE ROW LEVEL SECURITY;
                ALTER TABLE cross_predictions FORCE ROW LEVEL SECURITY;
                DROP POLICY IF EXISTS cross_predictions_tenant_isolation ON cross_predictions;
                CREATE POLICY cross_predictions_tenant_isolation ON cross_predictions
                    FOR ALL
                    USING (app_owner_or_admin(organization_id))
                    WITH CHECK (app_owner_or_admin(organization_id));
            END IF;
        END $$;
        """
    )

    # Performance indexes: org+created_at for high-volume tables.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='observations' AND column_name='organization_id')
               AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='observations' AND column_name='created_at') THEN
                CREATE INDEX IF NOT EXISTS idx_observations_org_created_at ON observations(organization_id, created_at DESC);
            END IF;

            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='messages' AND column_name='organization_id')
               AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='messages' AND column_name='created_at') THEN
                CREATE INDEX IF NOT EXISTS idx_messages_org_created_at ON messages(organization_id, created_at DESC);
            END IF;

            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='activity_logs' AND column_name='organization_id')
               AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='activity_logs' AND column_name='created_at') THEN
                CREATE INDEX IF NOT EXISTS idx_activity_logs_org_created_at ON activity_logs(organization_id, created_at DESC);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_activity_logs_org_created_at")
    op.execute("DROP INDEX IF EXISTS idx_messages_org_created_at")
    op.execute("DROP INDEX IF EXISTS idx_observations_org_created_at")

    op.execute("DROP POLICY IF EXISTS cross_predictions_tenant_isolation ON cross_predictions")
    op.execute("DROP POLICY IF EXISTS stability_results_tenant_isolation ON stability_results")
    op.execute("DROP POLICY IF EXISTS gs_models_tenant_isolation ON gs_models")
    op.execute("DROP FUNCTION IF EXISTS app_owner_or_admin(integer)")
