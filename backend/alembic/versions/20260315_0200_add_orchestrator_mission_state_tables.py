"""Add durable orchestrator mission-state tables.

Revision ID: 20260315_0200
Revises: 051_vajra_rls_perf_tuning
Create Date: 2026-03-15 02:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260315_0200"
down_revision = "20260313_0200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "orchestrator_missions",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("mission_id", sa.String(length=64), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("source_request", sa.Text(), nullable=False),
        sa.Column("final_summary", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mission_id", name="uq_orchestrator_mission_public_id"),
    )
    op.create_index(op.f("ix_orchestrator_missions_id"), "orchestrator_missions", ["id"], unique=False)
    op.create_index(op.f("ix_orchestrator_missions_mission_id"), "orchestrator_missions", ["mission_id"], unique=False)
    op.create_index(op.f("ix_orchestrator_missions_organization_id"), "orchestrator_missions", ["organization_id"], unique=False)
    op.create_index(op.f("ix_orchestrator_missions_priority"), "orchestrator_missions", ["priority"], unique=False)
    op.create_index(op.f("ix_orchestrator_missions_status"), "orchestrator_missions", ["status"], unique=False)
    op.create_index("ix_orchestrator_mission_org_status", "orchestrator_missions", ["organization_id", "status"], unique=False)

    op.create_table(
        "orchestrator_subtasks",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("mission_pk", sa.Integer(), nullable=False),
        sa.Column("subtask_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("owner_role", sa.String(length=255), nullable=False),
        sa.Column("depends_on", sa.JSON(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["mission_pk"], ["orchestrator_missions.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subtask_id", name="uq_orchestrator_subtask_public_id"),
    )
    op.create_index(op.f("ix_orchestrator_subtasks_id"), "orchestrator_subtasks", ["id"], unique=False)
    op.create_index(op.f("ix_orchestrator_subtasks_mission_pk"), "orchestrator_subtasks", ["mission_pk"], unique=False)
    op.create_index(op.f("ix_orchestrator_subtasks_organization_id"), "orchestrator_subtasks", ["organization_id"], unique=False)
    op.create_index(op.f("ix_orchestrator_subtasks_status"), "orchestrator_subtasks", ["status"], unique=False)
    op.create_index(op.f("ix_orchestrator_subtasks_subtask_id"), "orchestrator_subtasks", ["subtask_id"], unique=False)
    op.create_index("ix_orchestrator_subtask_mission_status", "orchestrator_subtasks", ["mission_pk", "status"], unique=False)

    op.create_table(
        "orchestrator_assignments",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("subtask_pk", sa.Integer(), nullable=False),
        sa.Column("assignment_id", sa.String(length=64), nullable=False),
        sa.Column("assigned_role", sa.String(length=255), nullable=False),
        sa.Column("handoff_reason", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["subtask_pk"], ["orchestrator_subtasks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assignment_id", name="uq_orchestrator_assignment_public_id"),
    )
    op.create_index(op.f("ix_orchestrator_assignments_assignment_id"), "orchestrator_assignments", ["assignment_id"], unique=False)
    op.create_index(op.f("ix_orchestrator_assignments_id"), "orchestrator_assignments", ["id"], unique=False)
    op.create_index(op.f("ix_orchestrator_assignments_organization_id"), "orchestrator_assignments", ["organization_id"], unique=False)
    op.create_index(op.f("ix_orchestrator_assignments_subtask_pk"), "orchestrator_assignments", ["subtask_pk"], unique=False)
    op.create_index("ix_orchestrator_assignment_subtask_role", "orchestrator_assignments", ["subtask_pk", "assigned_role"], unique=False)

    op.create_table(
        "orchestrator_evidence_items",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("mission_pk", sa.Integer(), nullable=True),
        sa.Column("subtask_pk", sa.Integer(), nullable=True),
        sa.Column("evidence_item_id", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("evidence_class", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["mission_pk"], ["orchestrator_missions.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["subtask_pk"], ["orchestrator_subtasks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evidence_item_id", name="uq_orchestrator_evidence_public_id"),
    )
    op.create_index(op.f("ix_orchestrator_evidence_items_evidence_class"), "orchestrator_evidence_items", ["evidence_class"], unique=False)
    op.create_index(op.f("ix_orchestrator_evidence_items_evidence_item_id"), "orchestrator_evidence_items", ["evidence_item_id"], unique=False)
    op.create_index(op.f("ix_orchestrator_evidence_items_id"), "orchestrator_evidence_items", ["id"], unique=False)
    op.create_index(op.f("ix_orchestrator_evidence_items_kind"), "orchestrator_evidence_items", ["kind"], unique=False)
    op.create_index(op.f("ix_orchestrator_evidence_items_mission_pk"), "orchestrator_evidence_items", ["mission_pk"], unique=False)
    op.create_index(op.f("ix_orchestrator_evidence_items_organization_id"), "orchestrator_evidence_items", ["organization_id"], unique=False)
    op.create_index(op.f("ix_orchestrator_evidence_items_subtask_pk"), "orchestrator_evidence_items", ["subtask_pk"], unique=False)
    op.create_index("ix_orchestrator_evidence_mission_kind", "orchestrator_evidence_items", ["mission_pk", "kind"], unique=False)
    op.create_index("ix_orchestrator_evidence_subtask_kind", "orchestrator_evidence_items", ["subtask_pk", "kind"], unique=False)

    op.create_table(
        "orchestrator_verification_runs",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("mission_pk", sa.Integer(), nullable=True),
        sa.Column("subtask_pk", sa.Integer(), nullable=True),
        sa.Column("verification_run_id", sa.String(length=64), nullable=False),
        sa.Column("verification_type", sa.String(length=64), nullable=False),
        sa.Column("result", sa.String(length=16), nullable=False),
        sa.Column("evidence_ref", sa.String(length=64), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["mission_pk"], ["orchestrator_missions.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["subtask_pk"], ["orchestrator_subtasks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("verification_run_id", name="uq_orchestrator_verification_public_id"),
    )
    op.create_index(op.f("ix_orchestrator_verification_runs_id"), "orchestrator_verification_runs", ["id"], unique=False)
    op.create_index(op.f("ix_orchestrator_verification_runs_mission_pk"), "orchestrator_verification_runs", ["mission_pk"], unique=False)
    op.create_index(op.f("ix_orchestrator_verification_runs_organization_id"), "orchestrator_verification_runs", ["organization_id"], unique=False)
    op.create_index(op.f("ix_orchestrator_verification_runs_result"), "orchestrator_verification_runs", ["result"], unique=False)
    op.create_index(op.f("ix_orchestrator_verification_runs_subtask_pk"), "orchestrator_verification_runs", ["subtask_pk"], unique=False)
    op.create_index(op.f("ix_orchestrator_verification_runs_verification_run_id"), "orchestrator_verification_runs", ["verification_run_id"], unique=False)
    op.create_index(op.f("ix_orchestrator_verification_runs_verification_type"), "orchestrator_verification_runs", ["verification_type"], unique=False)
    op.create_index("ix_orchestrator_verification_mission_type", "orchestrator_verification_runs", ["mission_pk", "verification_type"], unique=False)
    op.create_index("ix_orchestrator_verification_subtask_type", "orchestrator_verification_runs", ["subtask_pk", "verification_type"], unique=False)

    op.create_table(
        "orchestrator_decision_notes",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("mission_pk", sa.Integer(), nullable=False),
        sa.Column("decision_note_id", sa.String(length=64), nullable=False),
        sa.Column("decision_class", sa.String(length=64), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("authority_source", sa.String(length=255), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["mission_pk"], ["orchestrator_missions.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("decision_note_id", name="uq_orchestrator_decision_public_id"),
    )
    op.create_index(op.f("ix_orchestrator_decision_notes_decision_class"), "orchestrator_decision_notes", ["decision_class"], unique=False)
    op.create_index(op.f("ix_orchestrator_decision_notes_decision_note_id"), "orchestrator_decision_notes", ["decision_note_id"], unique=False)
    op.create_index(op.f("ix_orchestrator_decision_notes_id"), "orchestrator_decision_notes", ["id"], unique=False)
    op.create_index(op.f("ix_orchestrator_decision_notes_mission_pk"), "orchestrator_decision_notes", ["mission_pk"], unique=False)
    op.create_index(op.f("ix_orchestrator_decision_notes_organization_id"), "orchestrator_decision_notes", ["organization_id"], unique=False)
    op.create_index("ix_orchestrator_decision_mission_class", "orchestrator_decision_notes", ["mission_pk", "decision_class"], unique=False)

    op.create_table(
        "orchestrator_blockers",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("mission_pk", sa.Integer(), nullable=True),
        sa.Column("subtask_pk", sa.Integer(), nullable=True),
        sa.Column("blocker_id", sa.String(length=64), nullable=False),
        sa.Column("blocker_type", sa.String(length=64), nullable=False),
        sa.Column("impact", sa.Text(), nullable=False),
        sa.Column("escalation_needed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["mission_pk"], ["orchestrator_missions.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["subtask_pk"], ["orchestrator_subtasks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("blocker_id", name="uq_orchestrator_blocker_public_id"),
    )
    op.create_index(op.f("ix_orchestrator_blockers_blocker_id"), "orchestrator_blockers", ["blocker_id"], unique=False)
    op.create_index(op.f("ix_orchestrator_blockers_blocker_type"), "orchestrator_blockers", ["blocker_type"], unique=False)
    op.create_index(op.f("ix_orchestrator_blockers_id"), "orchestrator_blockers", ["id"], unique=False)
    op.create_index(op.f("ix_orchestrator_blockers_mission_pk"), "orchestrator_blockers", ["mission_pk"], unique=False)
    op.create_index(op.f("ix_orchestrator_blockers_organization_id"), "orchestrator_blockers", ["organization_id"], unique=False)
    op.create_index(op.f("ix_orchestrator_blockers_subtask_pk"), "orchestrator_blockers", ["subtask_pk"], unique=False)
    op.create_index("ix_orchestrator_blocker_mission_type", "orchestrator_blockers", ["mission_pk", "blocker_type"], unique=False)
    op.create_index("ix_orchestrator_blocker_subtask_type", "orchestrator_blockers", ["subtask_pk", "blocker_type"], unique=False)

    op.execute(
        """
        ALTER TABLE orchestrator_missions ENABLE ROW LEVEL SECURITY;
        ALTER TABLE orchestrator_missions FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS orchestrator_missions_tenant_isolation ON orchestrator_missions;
        CREATE POLICY orchestrator_missions_tenant_isolation ON orchestrator_missions
            FOR ALL
            USING (organization_id = current_organization_id() OR current_organization_id() = 0)
            WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0);

        ALTER TABLE orchestrator_subtasks ENABLE ROW LEVEL SECURITY;
        ALTER TABLE orchestrator_subtasks FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS orchestrator_subtasks_tenant_isolation ON orchestrator_subtasks;
        CREATE POLICY orchestrator_subtasks_tenant_isolation ON orchestrator_subtasks
            FOR ALL
            USING (organization_id = current_organization_id() OR current_organization_id() = 0)
            WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0);

        ALTER TABLE orchestrator_assignments ENABLE ROW LEVEL SECURITY;
        ALTER TABLE orchestrator_assignments FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS orchestrator_assignments_tenant_isolation ON orchestrator_assignments;
        CREATE POLICY orchestrator_assignments_tenant_isolation ON orchestrator_assignments
            FOR ALL
            USING (organization_id = current_organization_id() OR current_organization_id() = 0)
            WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0);

        ALTER TABLE orchestrator_evidence_items ENABLE ROW LEVEL SECURITY;
        ALTER TABLE orchestrator_evidence_items FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS orchestrator_evidence_items_tenant_isolation ON orchestrator_evidence_items;
        CREATE POLICY orchestrator_evidence_items_tenant_isolation ON orchestrator_evidence_items
            FOR ALL
            USING (organization_id = current_organization_id() OR current_organization_id() = 0)
            WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0);

        ALTER TABLE orchestrator_verification_runs ENABLE ROW LEVEL SECURITY;
        ALTER TABLE orchestrator_verification_runs FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS orchestrator_verification_runs_tenant_isolation ON orchestrator_verification_runs;
        CREATE POLICY orchestrator_verification_runs_tenant_isolation ON orchestrator_verification_runs
            FOR ALL
            USING (organization_id = current_organization_id() OR current_organization_id() = 0)
            WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0);

        ALTER TABLE orchestrator_decision_notes ENABLE ROW LEVEL SECURITY;
        ALTER TABLE orchestrator_decision_notes FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS orchestrator_decision_notes_tenant_isolation ON orchestrator_decision_notes;
        CREATE POLICY orchestrator_decision_notes_tenant_isolation ON orchestrator_decision_notes
            FOR ALL
            USING (organization_id = current_organization_id() OR current_organization_id() = 0)
            WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0);

        ALTER TABLE orchestrator_blockers ENABLE ROW LEVEL SECURITY;
        ALTER TABLE orchestrator_blockers FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS orchestrator_blockers_tenant_isolation ON orchestrator_blockers;
        CREATE POLICY orchestrator_blockers_tenant_isolation ON orchestrator_blockers
            FOR ALL
            USING (organization_id = current_organization_id() OR current_organization_id() = 0)
            WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0);
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS orchestrator_blockers_tenant_isolation ON orchestrator_blockers")
    op.execute("ALTER TABLE orchestrator_blockers DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS orchestrator_decision_notes_tenant_isolation ON orchestrator_decision_notes")
    op.execute("ALTER TABLE orchestrator_decision_notes DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS orchestrator_verification_runs_tenant_isolation ON orchestrator_verification_runs")
    op.execute("ALTER TABLE orchestrator_verification_runs DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS orchestrator_evidence_items_tenant_isolation ON orchestrator_evidence_items")
    op.execute("ALTER TABLE orchestrator_evidence_items DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS orchestrator_assignments_tenant_isolation ON orchestrator_assignments")
    op.execute("ALTER TABLE orchestrator_assignments DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS orchestrator_subtasks_tenant_isolation ON orchestrator_subtasks")
    op.execute("ALTER TABLE orchestrator_subtasks DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS orchestrator_missions_tenant_isolation ON orchestrator_missions")
    op.execute("ALTER TABLE orchestrator_missions DISABLE ROW LEVEL SECURITY")

    op.drop_index("ix_orchestrator_blocker_subtask_type", table_name="orchestrator_blockers")
    op.drop_index("ix_orchestrator_blocker_mission_type", table_name="orchestrator_blockers")
    op.drop_index(op.f("ix_orchestrator_blockers_subtask_pk"), table_name="orchestrator_blockers")
    op.drop_index(op.f("ix_orchestrator_blockers_organization_id"), table_name="orchestrator_blockers")
    op.drop_index(op.f("ix_orchestrator_blockers_mission_pk"), table_name="orchestrator_blockers")
    op.drop_index(op.f("ix_orchestrator_blockers_id"), table_name="orchestrator_blockers")
    op.drop_index(op.f("ix_orchestrator_blockers_blocker_type"), table_name="orchestrator_blockers")
    op.drop_index(op.f("ix_orchestrator_blockers_blocker_id"), table_name="orchestrator_blockers")
    op.drop_table("orchestrator_blockers")

    op.drop_index("ix_orchestrator_decision_mission_class", table_name="orchestrator_decision_notes")
    op.drop_index(op.f("ix_orchestrator_decision_notes_organization_id"), table_name="orchestrator_decision_notes")
    op.drop_index(op.f("ix_orchestrator_decision_notes_mission_pk"), table_name="orchestrator_decision_notes")
    op.drop_index(op.f("ix_orchestrator_decision_notes_id"), table_name="orchestrator_decision_notes")
    op.drop_index(op.f("ix_orchestrator_decision_notes_decision_note_id"), table_name="orchestrator_decision_notes")
    op.drop_index(op.f("ix_orchestrator_decision_notes_decision_class"), table_name="orchestrator_decision_notes")
    op.drop_table("orchestrator_decision_notes")

    op.drop_index("ix_orchestrator_verification_subtask_type", table_name="orchestrator_verification_runs")
    op.drop_index("ix_orchestrator_verification_mission_type", table_name="orchestrator_verification_runs")
    op.drop_index(op.f("ix_orchestrator_verification_runs_verification_type"), table_name="orchestrator_verification_runs")
    op.drop_index(op.f("ix_orchestrator_verification_runs_verification_run_id"), table_name="orchestrator_verification_runs")
    op.drop_index(op.f("ix_orchestrator_verification_runs_subtask_pk"), table_name="orchestrator_verification_runs")
    op.drop_index(op.f("ix_orchestrator_verification_runs_result"), table_name="orchestrator_verification_runs")
    op.drop_index(op.f("ix_orchestrator_verification_runs_organization_id"), table_name="orchestrator_verification_runs")
    op.drop_index(op.f("ix_orchestrator_verification_runs_mission_pk"), table_name="orchestrator_verification_runs")
    op.drop_index(op.f("ix_orchestrator_verification_runs_id"), table_name="orchestrator_verification_runs")
    op.drop_table("orchestrator_verification_runs")

    op.drop_index("ix_orchestrator_evidence_subtask_kind", table_name="orchestrator_evidence_items")
    op.drop_index("ix_orchestrator_evidence_mission_kind", table_name="orchestrator_evidence_items")
    op.drop_index(op.f("ix_orchestrator_evidence_items_subtask_pk"), table_name="orchestrator_evidence_items")
    op.drop_index(op.f("ix_orchestrator_evidence_items_organization_id"), table_name="orchestrator_evidence_items")
    op.drop_index(op.f("ix_orchestrator_evidence_items_mission_pk"), table_name="orchestrator_evidence_items")
    op.drop_index(op.f("ix_orchestrator_evidence_items_kind"), table_name="orchestrator_evidence_items")
    op.drop_index(op.f("ix_orchestrator_evidence_items_id"), table_name="orchestrator_evidence_items")
    op.drop_index(op.f("ix_orchestrator_evidence_items_evidence_item_id"), table_name="orchestrator_evidence_items")
    op.drop_index(op.f("ix_orchestrator_evidence_items_evidence_class"), table_name="orchestrator_evidence_items")
    op.drop_table("orchestrator_evidence_items")

    op.drop_index("ix_orchestrator_assignment_subtask_role", table_name="orchestrator_assignments")
    op.drop_index(op.f("ix_orchestrator_assignments_subtask_pk"), table_name="orchestrator_assignments")
    op.drop_index(op.f("ix_orchestrator_assignments_organization_id"), table_name="orchestrator_assignments")
    op.drop_index(op.f("ix_orchestrator_assignments_id"), table_name="orchestrator_assignments")
    op.drop_index(op.f("ix_orchestrator_assignments_assignment_id"), table_name="orchestrator_assignments")
    op.drop_table("orchestrator_assignments")

    op.drop_index("ix_orchestrator_subtask_mission_status", table_name="orchestrator_subtasks")
    op.drop_index(op.f("ix_orchestrator_subtasks_subtask_id"), table_name="orchestrator_subtasks")
    op.drop_index(op.f("ix_orchestrator_subtasks_status"), table_name="orchestrator_subtasks")
    op.drop_index(op.f("ix_orchestrator_subtasks_organization_id"), table_name="orchestrator_subtasks")
    op.drop_index(op.f("ix_orchestrator_subtasks_mission_pk"), table_name="orchestrator_subtasks")
    op.drop_index(op.f("ix_orchestrator_subtasks_id"), table_name="orchestrator_subtasks")
    op.drop_table("orchestrator_subtasks")

    op.drop_index("ix_orchestrator_mission_org_status", table_name="orchestrator_missions")
    op.drop_index(op.f("ix_orchestrator_missions_status"), table_name="orchestrator_missions")
    op.drop_index(op.f("ix_orchestrator_missions_priority"), table_name="orchestrator_missions")
    op.drop_index(op.f("ix_orchestrator_missions_organization_id"), table_name="orchestrator_missions")
    op.drop_index(op.f("ix_orchestrator_missions_mission_id"), table_name="orchestrator_missions")
    op.drop_index(op.f("ix_orchestrator_missions_id"), table_name="orchestrator_missions")
    op.drop_table("orchestrator_missions")