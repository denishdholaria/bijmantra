"""Add pg_trgm GIN indexes on searchable text columns.

Revision ID: 20260423_0900
Revises: 20260423_0800
Create Date: 2026-04-23 09:00:00.000000

Task 7.1: Create GIN indexes using gin_trgm_ops on text columns that are
          queried with ILIKE or similarity() in search services.

Indexed columns:
  - germplasm.germplasm_name          — primary germplasm search field
  - germplasm.default_display_name    — display name fuzzy search
  - users.full_name                   — user search by name
  - users.email                       — user search by email
  - programs.program_name             — program search
  - trials.trial_name                 — trial search
  - studies.study_name                — study search

Why GIN over GIST for text trigrams?
  GIN indexes are preferred for static or infrequently-updated text columns
  because they offer faster lookups at the cost of slower writes. GIST is
  better for frequently-updated columns. Germplasm names, user names, and
  program names change rarely, so GIN is the right choice here.

Why CONCURRENTLY?
  CREATE INDEX CONCURRENTLY builds the index without holding a table lock,
  allowing reads and writes to continue during the build. This is essential
  for production tables that may already contain data.

  IMPORTANT: CREATE INDEX CONCURRENTLY cannot run inside a transaction block.
  This migration commits the implicit Alembic transaction before executing
  the index creation statements.

ILIKE benefit:
  PostgreSQL automatically uses GIN (gin_trgm_ops) indexes for ILIKE '%term%'
  patterns when the extension is loaded. No query changes are needed — existing
  ILIKE queries in GermplasmSearchService.search() and other services will
  benefit automatically after this migration runs.

Requirement: 5.1, 5.2 (pg_trgm Index Hardening)
"""

import sqlalchemy as sa
from alembic import op


revision = "20260423_0900"
down_revision = "20260423_0800"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # CREATE INDEX CONCURRENTLY cannot run inside a transaction block.
    # Alembic wraps migrations in a transaction by default, so we must commit
    # the implicit transaction before issuing CONCURRENTLY index builds.
    # -------------------------------------------------------------------------
    connection = op.get_bind()
    connection.execute(sa.text("COMMIT"))

    indexes = [
        # germplasm table — primary search columns for breeder fuzzy search
        # Benefits: GermplasmSearchService.search() ILIKE on germplasm_name,
        #           and the new similarity_search() method.
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_germplasm_name_trgm "
        "ON germplasm USING GIN (germplasm_name gin_trgm_ops)",

        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_germplasm_display_name_trgm "
        "ON germplasm USING GIN (default_display_name gin_trgm_ops)",

        # users table — user search by name and email
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_full_name_trgm "
        "ON users USING GIN (full_name gin_trgm_ops)",

        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_trgm "
        "ON users USING GIN (email gin_trgm_ops)",

        # programs table — program search by name
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_programs_name_trgm "
        "ON programs USING GIN (program_name gin_trgm_ops)",

        # trials table — trial search by name
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trials_name_trgm "
        "ON trials USING GIN (trial_name gin_trgm_ops)",

        # studies table — study search by name
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_studies_name_trgm "
        "ON studies USING GIN (study_name gin_trgm_ops)",
    ]

    for idx_sql in indexes:
        connection.execute(sa.text(idx_sql))


def downgrade() -> None:
    # DROP INDEX CONCURRENTLY also cannot run inside a transaction block.
    connection = op.get_bind()
    connection.execute(sa.text("COMMIT"))

    drop_statements = [
        "DROP INDEX CONCURRENTLY IF EXISTS idx_germplasm_name_trgm",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_germplasm_display_name_trgm",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_users_full_name_trgm",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_users_email_trgm",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_programs_name_trgm",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_trials_name_trgm",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_studies_name_trgm",
    ]

    for drop_sql in drop_statements:
        connection.execute(sa.text(drop_sql))
