from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION = REPO_ROOT / "backend/alembic/versions/20260630_0100_add_seedlot_inventory_adjustments.py"


def test_seedlot_inventory_adjustment_migration_declares_append_only_ledger() -> None:
    source = MIGRATION.read_text()

    for required in [
        'revision = "20260630_0100"',
        'down_revision = "20260529_0100"',
        'TABLE_NAME = "seedlot_inventory_adjustments"',
        'ACTION = "seedlot_inventory_adjustment.create"',
        'AUDIT_EVENT = "seed_lot.adjusted"',
        'sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False)',
        'sa.Column("public_id", postgresql.UUID(as_uuid=True), nullable=False)',
        'sa.Column("organization_id", sa.BigInteger(), nullable=False)',
        'sa.Column("seedlot_id", sa.BigInteger(), nullable=True)',
        'sa.Column("quantity_delta", sa.Numeric(20, 6), nullable=False)',
        'sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True)',
        'sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())',
        'sa.Column("reversal_of_public_id", postgresql.UUID(as_uuid=True), nullable=True)',
        'sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True)',
        'sa.UniqueConstraint("public_id", name="uq_seedlot_inventory_adjustments_public_id")',
        "uq_seedlot_inventory_adjustments_idempotency",
        "ck_seedlot_inventory_adjustments_public_id_uuid7",
        "ck_seedlot_inventory_adjustments_quantity_nonzero",
        "ck_seedlot_inventory_adjustments_reason_nonempty",
        "ck_seedlot_inventory_adjustments_audit_event",
        "ck_seedlot_inventory_adjustments_action",
        "ENABLE ROW LEVEL SECURITY",
    ]:
        assert required in source


def test_seedlot_inventory_adjustment_migration_does_not_alter_seedlots() -> None:
    source = MIGRATION.read_text()

    for forbidden in [
        'op.add_column("seedlots"',
        "op.add_column('seedlots'",
        "ALTER TABLE seedlots ADD COLUMN",
        "UPDATE seedlots SET",
        "DELETE FROM seedlots",
        'sa.Column("deleted_at"',
        'sa.Column("deleted_by_user_id"',
    ]:
        assert forbidden not in source
