"""Add persisted vision dataset tables.

Revision ID: 20260328_1200
Revises: 20260323_0200
Create Date: 2026-03-28 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260328_1200"
down_revision = "20260323_0200"
branch_labels = None
depends_on = None


dataset_type_enum = postgresql.ENUM(
    "CLASSIFICATION",
    "DETECTION",
    "SEGMENTATION",
    name="visiondatasettype",
    create_type=False,
)
dataset_status_enum = postgresql.ENUM(
    "DRAFT",
    "COLLECTING",
    "ANNOTATING",
    "READY",
    "TRAINING",
    name="visiondatasetstatus",
    create_type=False,
)


def _enable_tenant_rls(table_name: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = '{table_name}'
                AND column_name = 'organization_id'
            ) THEN
                ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;
                ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY;
                DROP POLICY IF EXISTS {table_name}_tenant_isolation ON {table_name};
                CREATE POLICY {table_name}_tenant_isolation ON {table_name}
                    FOR ALL
                    USING (
                        current_organization_id() = 0
                        OR organization_id = current_organization_id()
                    )
                    WITH CHECK (
                        current_organization_id() = 0
                        OR organization_id = current_organization_id()
                    );
            END IF;
        END $$;
        """
    )


def _disable_tenant_rls(table_name: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = '{table_name}'
            ) THEN
                DROP POLICY IF EXISTS {table_name}_tenant_isolation ON {table_name};
                ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;
            END IF;
        END $$;
        """
    )


def _table_exists(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _column_map(table_name: str) -> dict[str, dict[str, object]]:
    return {
        column["name"]: column for column in sa.inspect(op.get_bind()).get_columns(table_name)
    }


def _index_names(table_name: str) -> set[str]:
    if not _table_exists(table_name):
        return set()
    return {
        index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)
    }


def _create_vision_datasets_table() -> None:
    op.create_table(
        "vision_datasets",
        sa.Column("dataset_code", sa.String(length=64), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("dataset_type", dataset_type_enum, nullable=False),
        sa.Column("crop", sa.String(length=100), nullable=False),
        sa.Column("classes", sa.JSON(), nullable=False),
        sa.Column("train_split", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("val_split", sa.Float(), nullable=False, server_default="0.15"),
        sa.Column("test_split", sa.Float(), nullable=False, server_default="0.15"),
        sa.Column("status", dataset_status_enum, nullable=False, server_default="DRAFT"),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def _upgrade_legacy_vision_datasets_table() -> None:
    columns = _column_map("vision_datasets")

    if "dataset_code" not in columns:
        op.add_column(
            "vision_datasets",
            sa.Column("dataset_code", sa.String(length=64), nullable=True),
        )
    if "train_split" not in columns:
        op.add_column(
            "vision_datasets",
            sa.Column("train_split", sa.Float(), nullable=True),
        )
    if "val_split" not in columns:
        op.add_column(
            "vision_datasets",
            sa.Column("val_split", sa.Float(), nullable=True),
        )
    if "test_split" not in columns:
        op.add_column(
            "vision_datasets",
            sa.Column("test_split", sa.Float(), nullable=True),
        )
    if "created_by" not in columns:
        op.add_column(
            "vision_datasets",
            sa.Column("created_by", sa.String(), nullable=True),
        )

    columns = _column_map("vision_datasets")

    op.execute(
        """
        UPDATE vision_datasets
        SET dataset_code = CONCAT('vision-dataset-', id)
        WHERE dataset_code IS NULL OR btrim(dataset_code) = ''
        """
    )

    if "splits" in columns:
        op.execute(
            """
            UPDATE vision_datasets
            SET train_split = COALESCE(train_split, NULLIF(splits ->> 'train', '')::double precision, 0.7),
                val_split = COALESCE(val_split, NULLIF(splits ->> 'val', '')::double precision, 0.15),
                test_split = COALESCE(test_split, NULLIF(splits ->> 'test', '')::double precision, 0.15)
            WHERE train_split IS NULL OR val_split IS NULL OR test_split IS NULL
            """
        )
    else:
        op.execute(
            """
            UPDATE vision_datasets
            SET train_split = COALESCE(train_split, 0.7),
                val_split = COALESCE(val_split, 0.15),
                test_split = COALESCE(test_split, 0.15)
            WHERE train_split IS NULL OR val_split IS NULL OR test_split IS NULL
            """
        )

    op.execute(
        """
        UPDATE vision_datasets
        SET classes = '[]'::json
        WHERE classes IS NULL
        """
    )
    op.execute(
        """
        UPDATE vision_datasets
        SET dataset_type = CASE
            WHEN dataset_type IS NULL OR btrim(dataset_type::text) = '' THEN 'CLASSIFICATION'
            WHEN upper(dataset_type::text) IN ('CLASSIFICATION', 'DETECTION', 'SEGMENTATION')
                THEN upper(dataset_type::text)
            ELSE 'CLASSIFICATION'
        END
        """
    )
    op.execute(
        """
        UPDATE vision_datasets
        SET status = CASE
            WHEN status IS NULL OR btrim(status::text) = '' THEN 'DRAFT'
            WHEN upper(status::text) IN ('DRAFT', 'COLLECTING', 'ANNOTATING', 'READY', 'TRAINING')
                THEN upper(status::text)
            ELSE 'DRAFT'
        END
        """
    )

    columns = _column_map("vision_datasets")
    if str(columns["dataset_type"]["type"]).lower() != "visiondatasettype":
        op.execute(
            """
            ALTER TABLE vision_datasets
            ALTER COLUMN dataset_type TYPE visiondatasettype
            USING dataset_type::visiondatasettype
            """
        )
    if str(columns["status"]["type"]).lower() != "visiondatasetstatus":
        op.execute(
            """
            ALTER TABLE vision_datasets
            ALTER COLUMN status TYPE visiondatasetstatus
            USING status::visiondatasetstatus
            """
        )

    op.execute(
        """
        ALTER TABLE vision_datasets
        ALTER COLUMN dataset_code SET NOT NULL,
        ALTER COLUMN classes SET DEFAULT '[]'::json,
        ALTER COLUMN classes SET NOT NULL,
        ALTER COLUMN train_split SET DEFAULT 0.7,
        ALTER COLUMN train_split SET NOT NULL,
        ALTER COLUMN val_split SET DEFAULT 0.15,
        ALTER COLUMN val_split SET NOT NULL,
        ALTER COLUMN test_split SET DEFAULT 0.15,
        ALTER COLUMN test_split SET NOT NULL,
        ALTER COLUMN dataset_type SET DEFAULT 'CLASSIFICATION',
        ALTER COLUMN dataset_type SET NOT NULL,
        ALTER COLUMN status SET DEFAULT 'DRAFT',
        ALTER COLUMN status SET NOT NULL
        """
    )


def _ensure_vision_dataset_indexes() -> None:
    index_names = _index_names("vision_datasets")
    if op.f("ix_vision_datasets_id") not in index_names:
        op.create_index(op.f("ix_vision_datasets_id"), "vision_datasets", ["id"], unique=False)
    if "ix_vision_datasets_dataset_code" not in index_names:
        op.create_index("ix_vision_datasets_dataset_code", "vision_datasets", ["dataset_code"], unique=True)
    if "ix_vision_datasets_organization_id" not in index_names:
        op.create_index("ix_vision_datasets_organization_id", "vision_datasets", ["organization_id"], unique=False)
    if "ix_vision_datasets_crop" not in index_names:
        op.create_index("ix_vision_datasets_crop", "vision_datasets", ["crop"], unique=False)
    if "ix_vision_datasets_status" not in index_names:
        op.create_index("ix_vision_datasets_status", "vision_datasets", ["status"], unique=False)


def _create_vision_dataset_images_table() -> None:
    op.create_table(
        "vision_dataset_images",
        sa.Column("image_code", sa.String(length=64), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("height", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("split", sa.String(length=16), nullable=False, server_default="train"),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("annotation_data", sa.JSON(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["dataset_id"], ["vision_datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def _ensure_vision_dataset_images_indexes() -> None:
    index_names = _index_names("vision_dataset_images")
    if op.f("ix_vision_dataset_images_id") not in index_names:
        op.create_index(op.f("ix_vision_dataset_images_id"), "vision_dataset_images", ["id"], unique=False)
    if "ix_vision_dataset_images_image_code" not in index_names:
        op.create_index("ix_vision_dataset_images_image_code", "vision_dataset_images", ["image_code"], unique=True)
    if "ix_vision_dataset_images_dataset_id" not in index_names:
        op.create_index("ix_vision_dataset_images_dataset_id", "vision_dataset_images", ["dataset_id"], unique=False)
    if "ix_vision_dataset_images_organization_id" not in index_names:
        op.create_index("ix_vision_dataset_images_organization_id", "vision_dataset_images", ["organization_id"], unique=False)
    if "ix_vision_dataset_images_split" not in index_names:
        op.create_index("ix_vision_dataset_images_split", "vision_dataset_images", ["split"], unique=False)


def upgrade() -> None:
    dataset_type_enum.create(op.get_bind(), checkfirst=True)
    dataset_status_enum.create(op.get_bind(), checkfirst=True)

    if not _table_exists("vision_datasets"):
        _create_vision_datasets_table()
    else:
        _upgrade_legacy_vision_datasets_table()
    _ensure_vision_dataset_indexes()

    if not _table_exists("vision_dataset_images"):
        _create_vision_dataset_images_table()
    _ensure_vision_dataset_images_indexes()

    _enable_tenant_rls("vision_datasets")
    _enable_tenant_rls("vision_dataset_images")


def downgrade() -> None:
    _disable_tenant_rls("vision_dataset_images")
    _disable_tenant_rls("vision_datasets")

    op.drop_index("ix_vision_dataset_images_split", table_name="vision_dataset_images")
    op.drop_index("ix_vision_dataset_images_organization_id", table_name="vision_dataset_images")
    op.drop_index("ix_vision_dataset_images_dataset_id", table_name="vision_dataset_images")
    op.drop_index("ix_vision_dataset_images_image_code", table_name="vision_dataset_images")
    op.drop_index(op.f("ix_vision_dataset_images_id"), table_name="vision_dataset_images")
    op.drop_table("vision_dataset_images")

    op.drop_index("ix_vision_datasets_status", table_name="vision_datasets")
    op.drop_index("ix_vision_datasets_crop", table_name="vision_datasets")
    op.drop_index("ix_vision_datasets_organization_id", table_name="vision_datasets")
    op.drop_index("ix_vision_datasets_dataset_code", table_name="vision_datasets")
    op.drop_index(op.f("ix_vision_datasets_id"), table_name="vision_datasets")
    op.drop_table("vision_datasets")

    sa.Enum(name="visiondatasetstatus").drop(op.get_bind(), checkfirst=True)