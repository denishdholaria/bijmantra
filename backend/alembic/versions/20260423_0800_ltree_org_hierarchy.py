"""Add ltree-based organization hierarchy support.

Revision ID: 20260423_0800
Revises: 20260423_0700
Create Date: 2026-04-23 08:00:00.000000

Task 6.2: Add parent_id FK column and org_path ltree column to organizations table.
          Populate org_path for all existing orgs (flat roots — no parent data exists).
          Add GIST index on org_path for efficient ancestor/descendant queries.

Task 6.3: Create trigger function update_org_path() that automatically maintains
          org_path whenever parent_id is set or changed on INSERT or UPDATE.

Task 6.4: Create utility function get_org_subtree(p_org_id) that returns all
          descendant org IDs for a given organization using ltree <@ operator.

ltree label format: 'org_<id>'
  - Labels must start with a letter or underscore (not a digit), so we prefix with 'org_'.
  - Hierarchy example: root org 1 → 'org_1', child org 5 under org 1 → 'org_1.org_5'.

Query patterns enabled:
  -- All descendants of org 1
  SELECT * FROM organizations WHERE org_path <@ 'org_1';

  -- All ancestors of org 5
  SELECT * FROM organizations WHERE org_path @> (
      SELECT org_path FROM organizations WHERE id = 5
  );

  -- Direct children only
  SELECT * FROM organizations WHERE org_path ~ 'org_1.*{1}';
"""

import sqlalchemy as sa
from alembic import op


revision = "20260423_0800"
down_revision = "20260423_0700"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # Step 1: Add parent_id self-referential FK column
    # -------------------------------------------------------------------------
    op.add_column("organizations", sa.Column("parent_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_organizations_parent_id",
        "organizations",
        "organizations",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_organizations_parent_id", "organizations", ["parent_id"])

    # -------------------------------------------------------------------------
    # Step 2: Add org_path ltree column
    # -------------------------------------------------------------------------
    # Use raw SQL — SQLAlchemy has no native ltree type mapping.
    op.execute("ALTER TABLE organizations ADD COLUMN org_path ltree")

    # -------------------------------------------------------------------------
    # Step 3: Populate org_path for existing orgs
    # All existing orgs are flat roots (no parent-child data exists yet).
    # Format: 'org_<id>' — ltree labels must start with a letter or underscore.
    # -------------------------------------------------------------------------
    op.execute("""
        UPDATE organizations
        SET org_path = ('org_' || id::text)::ltree
        WHERE parent_id IS NULL
    """)

    # -------------------------------------------------------------------------
    # Step 4: Add GIST index on org_path for efficient ancestor/descendant queries
    # -------------------------------------------------------------------------
    op.execute(
        "CREATE INDEX idx_organizations_org_path ON organizations USING GIST (org_path)"
    )

    # -------------------------------------------------------------------------
    # Step 5: Create trigger function — maintains org_path on INSERT/UPDATE
    # -------------------------------------------------------------------------
    # The trigger fires BEFORE INSERT OR UPDATE OF parent_id so that NEW.org_path
    # is set correctly before the row is written.
    #
    # Logic:
    #   - If parent_id IS NULL  → root node: org_path = 'org_<id>'
    #   - If parent_id IS SET   → child node: org_path = parent.org_path || 'org_<id>'
    #
    # Raises an exception if the parent row has no org_path yet (data integrity guard).
    op.execute("""
        CREATE OR REPLACE FUNCTION update_org_path()
        RETURNS TRIGGER AS $$
        DECLARE
            parent_path ltree;
        BEGIN
            IF NEW.parent_id IS NULL THEN
                NEW.org_path := ('org_' || NEW.id::text)::ltree;
            ELSE
                SELECT org_path INTO parent_path
                FROM organizations
                WHERE id = NEW.parent_id;

                IF parent_path IS NULL THEN
                    RAISE EXCEPTION 'Parent organization % has no org_path set', NEW.parent_id;
                END IF;

                NEW.org_path := parent_path || ('org_' || NEW.id::text)::ltree;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # -------------------------------------------------------------------------
    # Step 6: Attach trigger to organizations table
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE TRIGGER trg_update_org_path
        BEFORE INSERT OR UPDATE OF parent_id
        ON organizations
        FOR EACH ROW
        EXECUTE FUNCTION update_org_path()
    """)

    # -------------------------------------------------------------------------
    # Step 7: Create utility function get_org_subtree(p_org_id)
    # -------------------------------------------------------------------------
    # Returns all descendant org IDs (excluding the root org itself) using the
    # ltree <@ (is-descendant-of) operator against the GIST index.
    #
    # Returns an empty result set if the org does not exist or has no org_path.
    op.execute("""
        CREATE OR REPLACE FUNCTION get_org_subtree(p_org_id integer)
        RETURNS TABLE(org_id integer) AS $$
        DECLARE
            root_path ltree;
        BEGIN
            SELECT org_path INTO root_path
            FROM organizations
            WHERE id = p_org_id;

            IF root_path IS NULL THEN
                RETURN;
            END IF;

            RETURN QUERY
            SELECT id
            FROM organizations
            WHERE org_path <@ root_path
              AND id != p_org_id;
        END;
        $$ LANGUAGE plpgsql STABLE;
    """)


def downgrade() -> None:
    # Drop in reverse dependency order
    op.execute("DROP FUNCTION IF EXISTS get_org_subtree(integer)")
    op.execute("DROP TRIGGER IF EXISTS trg_update_org_path ON organizations")
    op.execute("DROP FUNCTION IF EXISTS update_org_path()")
    op.execute("DROP INDEX IF EXISTS idx_organizations_org_path")
    op.execute("ALTER TABLE organizations DROP COLUMN IF EXISTS org_path")
    op.drop_index("ix_organizations_parent_id", table_name="organizations")
    op.drop_constraint("fk_organizations_parent_id", "organizations", type_="foreignkey")
    op.drop_column("organizations", "parent_id")
