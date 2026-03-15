"""Backfill ADR-006 ownership columns and RLS for DevGuru and Veena v2 tables.

Revision ID: 20260313_0200
Revises: 20260311_0400
Create Date: 2026-03-13 02:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260313_0200"
down_revision = "20260311_0400"
branch_labels = None
depends_on = None


def _current_org_sql() -> str:
    return "COALESCE(NULLIF(current_setting('app.current_organization_id', true), ''), '-1')::integer"


def _current_user_sql() -> str:
    return "COALESCE(NULLIF(current_setting('app.current_user_id', true), ''), '-1')::integer"


def _generic_rls_sql(table_name: str) -> str:
    current_org_sql = _current_org_sql()
    return f"""
ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS {table_name}_tenant_isolation ON {table_name};
CREATE POLICY {table_name}_tenant_isolation ON {table_name}
    FOR ALL
    USING (
        {current_org_sql} = 0
        OR organization_id = {current_org_sql}
    )
    WITH CHECK (
        {current_org_sql} = 0
        OR organization_id = {current_org_sql}
    );
"""


def _user_owned_rls_sql(table_name: str) -> str:
    current_org_sql = _current_org_sql()
    current_user_sql = _current_user_sql()
    drop_legacy_policy_sql = ""
    if table_name == "veena_memories_v2":
        drop_legacy_policy_sql = "DROP POLICY IF EXISTS veena_memories_v2_user_scope ON veena_memories_v2;\n"

    return f"""
ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS {table_name}_tenant_isolation ON {table_name};
{drop_legacy_policy_sql}CREATE POLICY {table_name}_tenant_isolation ON {table_name}
    FOR ALL
    USING (
        {current_org_sql} = 0
        OR (
            organization_id = {current_org_sql}
            AND user_id = {current_user_sql}
        )
    )
    WITH CHECK (
        {current_org_sql} = 0
        OR (
            organization_id = {current_org_sql}
            AND user_id = {current_user_sql}
        )
    );
"""


def _reasoning_trace_rls_sql() -> str:
    current_org_sql = _current_org_sql()
    current_user_sql = _current_user_sql()
    return f"""
ALTER TABLE veena_reasoning_traces_v2 ENABLE ROW LEVEL SECURITY;
ALTER TABLE veena_reasoning_traces_v2 FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS veena_reasoning_traces_v2_tenant_isolation ON veena_reasoning_traces_v2;
CREATE POLICY veena_reasoning_traces_v2_tenant_isolation ON veena_reasoning_traces_v2
    FOR ALL
    USING (
        {current_org_sql} = 0
        OR (
            organization_id = {current_org_sql}
            AND EXISTS (
                SELECT 1
                FROM veena_audit_logs audit
                WHERE audit.session_id = veena_reasoning_traces_v2.session_id
                  AND audit.organization_id = {current_org_sql}
                  AND audit.user_id = {current_user_sql}
            )
        )
    )
    WITH CHECK (
        {current_org_sql} = 0
        OR (
            organization_id = {current_org_sql}
            AND EXISTS (
                SELECT 1
                FROM veena_audit_logs audit
                WHERE audit.session_id = veena_reasoning_traces_v2.session_id
                  AND audit.organization_id = {current_org_sql}
                  AND audit.user_id = {current_user_sql}
            )
        )
    );
"""


def _ensure_no_nulls(table_name: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM {table_name} WHERE organization_id IS NULL
            ) THEN
                RAISE EXCEPTION 'ADR-006 backfill failed: %.organization_id still has unresolved rows', '{table_name}';
            END IF;
        END $$;
        """
    )


def upgrade() -> None:
    op.add_column("research_projects", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE research_projects AS project
        SET organization_id = users.organization_id
        FROM users
        WHERE project.organization_id IS NULL
          AND project.user_id = users.id;
        """
    )
    op.execute(
        """
        UPDATE research_projects AS project
        SET organization_id = programs.organization_id
        FROM programs
        WHERE project.organization_id IS NULL
          AND project.program_id = programs.id;
        """
    )
    _ensure_no_nulls("research_projects")
    op.alter_column("research_projects", "organization_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key("fk_research_projects_organization_id_organizations", "research_projects", "organizations", ["organization_id"], ["id"])
    op.create_index("ix_research_projects_organization_id", "research_projects", ["organization_id"], unique=False)

    op.add_column("paper_experiment_links", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE paper_experiment_links AS link
        SET organization_id = project.organization_id
        FROM research_papers AS paper
        JOIN research_projects AS project ON project.id = paper.project_id
        WHERE link.organization_id IS NULL
          AND link.paper_id = paper.id;
        """
    )
    _ensure_no_nulls("paper_experiment_links")
    op.alter_column("paper_experiment_links", "organization_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key("fk_paper_experiment_links_organization_id_organizations", "paper_experiment_links", "organizations", ["organization_id"], ["id"])
    op.create_index("ix_paper_experiment_links_organization_id", "paper_experiment_links", ["organization_id"], unique=False)

    op.add_column("writing_sessions", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE writing_sessions AS session
        SET organization_id = project.organization_id
        FROM thesis_chapters AS chapter
        JOIN research_projects AS project ON project.id = chapter.project_id
        WHERE session.organization_id IS NULL
          AND session.chapter_id = chapter.id;
        """
    )
    _ensure_no_nulls("writing_sessions")
    op.alter_column("writing_sessions", "organization_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key("fk_writing_sessions_organization_id_organizations", "writing_sessions", "organizations", ["organization_id"], ["id"])
    op.create_index("ix_writing_sessions_organization_id", "writing_sessions", ["organization_id"], unique=False)

    op.add_column("committee_members", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE committee_members AS member
        SET organization_id = project.organization_id
        FROM research_projects AS project
        WHERE member.organization_id IS NULL
          AND member.project_id = project.id;
        """
    )
    _ensure_no_nulls("committee_members")
    op.alter_column("committee_members", "organization_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key("fk_committee_members_organization_id_organizations", "committee_members", "organizations", ["organization_id"], ["id"])
    op.create_index("ix_committee_members_organization_id", "committee_members", ["organization_id"], unique=False)

    op.add_column("committee_meetings", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE committee_meetings AS meeting
        SET organization_id = project.organization_id
        FROM research_projects AS project
        WHERE meeting.organization_id IS NULL
          AND meeting.project_id = project.id;
        """
    )
    _ensure_no_nulls("committee_meetings")
    op.alter_column("committee_meetings", "organization_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key("fk_committee_meetings_organization_id_organizations", "committee_meetings", "organizations", ["organization_id"], ["id"])
    op.create_index("ix_committee_meetings_organization_id", "committee_meetings", ["organization_id"], unique=False)

    op.add_column("feedback_items", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE feedback_items AS feedback
        SET organization_id = project.organization_id
        FROM research_projects AS project
        WHERE feedback.organization_id IS NULL
          AND feedback.project_id = project.id;
        """
    )
    _ensure_no_nulls("feedback_items")
    op.alter_column("feedback_items", "organization_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key("fk_feedback_items_organization_id_organizations", "feedback_items", "organizations", ["organization_id"], ["id"])
    op.create_index("ix_feedback_items_organization_id", "feedback_items", ["organization_id"], unique=False)

    op.add_column("veena_memories_v2", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE veena_memories_v2 AS memory
        SET organization_id = users.organization_id
        FROM users
        WHERE memory.organization_id IS NULL
          AND memory.user_id = users.id;
        """
    )
    _ensure_no_nulls("veena_memories_v2")
    op.alter_column("veena_memories_v2", "organization_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key("fk_veena_memories_v2_organization_id_organizations", "veena_memories_v2", "organizations", ["organization_id"], ["id"])
    op.create_index("ix_veena_memories_v2_org_id", "veena_memories_v2", ["organization_id"], unique=False)

    op.add_column("veena_user_contexts_v2", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE veena_user_contexts_v2 AS context
        SET organization_id = users.organization_id
        FROM users
        WHERE context.organization_id IS NULL
          AND context.user_id = users.id;
        """
    )
    _ensure_no_nulls("veena_user_contexts_v2")
    op.alter_column("veena_user_contexts_v2", "organization_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key("fk_veena_user_contexts_v2_organization_id_organizations", "veena_user_contexts_v2", "organizations", ["organization_id"], ["id"])
    op.create_index("ix_veena_user_contexts_v2_org_id", "veena_user_contexts_v2", ["organization_id"], unique=False)

    op.add_column("veena_audit_logs", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE veena_audit_logs AS audit
        SET organization_id = users.organization_id
        FROM users
        WHERE audit.organization_id IS NULL
          AND audit.user_id = users.id;
        """
    )
    _ensure_no_nulls("veena_audit_logs")
    op.alter_column("veena_audit_logs", "organization_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key("fk_veena_audit_logs_organization_id_organizations", "veena_audit_logs", "organizations", ["organization_id"], ["id"])
    op.create_index("ix_veena_audit_logs_organization_id", "veena_audit_logs", ["organization_id"], unique=False)

    op.add_column("veena_reasoning_traces_v2", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.execute(
        """
        WITH session_ownership AS (
            SELECT
                audit.session_id,
                MIN(audit.organization_id) AS organization_id,
                COUNT(DISTINCT audit.organization_id) AS organization_count
            FROM veena_audit_logs AS audit
            WHERE audit.session_id IS NOT NULL
              AND audit.organization_id IS NOT NULL
            GROUP BY audit.session_id
        )
        UPDATE veena_reasoning_traces_v2 AS trace
        SET organization_id = session_ownership.organization_id
        FROM session_ownership
        WHERE trace.organization_id IS NULL
          AND trace.session_id = session_ownership.session_id
          AND session_ownership.organization_count = 1;
        """
    )
    _ensure_no_nulls("veena_reasoning_traces_v2")
    op.alter_column("veena_reasoning_traces_v2", "organization_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key("fk_veena_reasoning_traces_v2_organization_id_organizations", "veena_reasoning_traces_v2", "organizations", ["organization_id"], ["id"])
    op.create_index("ix_reasoning_trace_v2_org_id", "veena_reasoning_traces_v2", ["organization_id"], unique=False)

    op.execute(_generic_rls_sql("research_projects"))
    op.execute(_generic_rls_sql("paper_experiment_links"))
    op.execute(_generic_rls_sql("writing_sessions"))
    op.execute(_generic_rls_sql("committee_members"))
    op.execute(_generic_rls_sql("committee_meetings"))
    op.execute(_generic_rls_sql("feedback_items"))
    op.execute(_user_owned_rls_sql("veena_memories_v2"))
    op.execute(_user_owned_rls_sql("veena_user_contexts_v2"))
    op.execute(_user_owned_rls_sql("veena_audit_logs"))
    op.execute(_reasoning_trace_rls_sql())


def downgrade() -> None:
    for table_name in [
        "feedback_items",
        "committee_meetings",
        "committee_members",
        "writing_sessions",
        "paper_experiment_links",
        "research_projects",
        "veena_reasoning_traces_v2",
        "veena_audit_logs",
        "veena_user_contexts_v2",
        "veena_memories_v2",
    ]:
        op.execute(f"DROP POLICY IF EXISTS {table_name}_tenant_isolation ON {table_name}")
        op.execute(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY")

    op.execute(
        """
        ALTER TABLE veena_memories_v2 ENABLE ROW LEVEL SECURITY;
        CREATE POLICY veena_memories_v2_user_scope
        ON veena_memories_v2
        USING (user_id = COALESCE(NULLIF(current_setting('app.current_user_id', true), ''), '-1')::int);
        """
    )

    op.drop_index("ix_reasoning_trace_v2_org_id", table_name="veena_reasoning_traces_v2")
    op.drop_constraint("fk_veena_reasoning_traces_v2_organization_id_organizations", "veena_reasoning_traces_v2", type_="foreignkey")
    op.drop_column("veena_reasoning_traces_v2", "organization_id")

    op.drop_index("ix_veena_audit_logs_organization_id", table_name="veena_audit_logs")
    op.drop_constraint("fk_veena_audit_logs_organization_id_organizations", "veena_audit_logs", type_="foreignkey")
    op.drop_column("veena_audit_logs", "organization_id")

    op.drop_index("ix_veena_user_contexts_v2_org_id", table_name="veena_user_contexts_v2")
    op.drop_constraint("fk_veena_user_contexts_v2_organization_id_organizations", "veena_user_contexts_v2", type_="foreignkey")
    op.drop_column("veena_user_contexts_v2", "organization_id")

    op.drop_index("ix_veena_memories_v2_org_id", table_name="veena_memories_v2")
    op.drop_constraint("fk_veena_memories_v2_organization_id_organizations", "veena_memories_v2", type_="foreignkey")
    op.drop_column("veena_memories_v2", "organization_id")

    op.drop_index("ix_feedback_items_organization_id", table_name="feedback_items")
    op.drop_constraint("fk_feedback_items_organization_id_organizations", "feedback_items", type_="foreignkey")
    op.drop_column("feedback_items", "organization_id")

    op.drop_index("ix_committee_meetings_organization_id", table_name="committee_meetings")
    op.drop_constraint("fk_committee_meetings_organization_id_organizations", "committee_meetings", type_="foreignkey")
    op.drop_column("committee_meetings", "organization_id")

    op.drop_index("ix_committee_members_organization_id", table_name="committee_members")
    op.drop_constraint("fk_committee_members_organization_id_organizations", "committee_members", type_="foreignkey")
    op.drop_column("committee_members", "organization_id")

    op.drop_index("ix_writing_sessions_organization_id", table_name="writing_sessions")
    op.drop_constraint("fk_writing_sessions_organization_id_organizations", "writing_sessions", type_="foreignkey")
    op.drop_column("writing_sessions", "organization_id")

    op.drop_index("ix_paper_experiment_links_organization_id", table_name="paper_experiment_links")
    op.drop_constraint("fk_paper_experiment_links_organization_id_organizations", "paper_experiment_links", type_="foreignkey")
    op.drop_column("paper_experiment_links", "organization_id")

    op.drop_index("ix_research_projects_organization_id", table_name="research_projects")
    op.drop_constraint("fk_research_projects_organization_id_organizations", "research_projects", type_="foreignkey")
    op.drop_column("research_projects", "organization_id")