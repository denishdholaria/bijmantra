"""Restore BrAPI phenotyping reference tables.

Revision ID: 20260512_0100
Revises: 20260508_0100
Create Date: 2026-05-12 19:30:00.000000
"""

from alembic import op

revision = "20260512_0100"
down_revision = "20260508_0100"
branch_labels = None
depends_on = None


REFERENCE_TABLES = (
    "scales",
    "methods",
    "observation_levels",
    "traits",
    "germplasm_attribute_definitions",
    "germplasm_attribute_values",
)


def _enable_tenant_rls(table_name: str) -> None:
    op.execute(
        f"""
        ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY;
        ALTER TABLE "{table_name}" FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS {table_name}_tenant_isolation ON "{table_name}";
        CREATE POLICY {table_name}_tenant_isolation ON "{table_name}"
            FOR ALL
            USING (
                current_organization_id() = 0
                OR organization_id = current_organization_id()
            )
            WITH CHECK (
                current_organization_id() = 0
                OR organization_id = current_organization_id()
            );
        CREATE INDEX IF NOT EXISTS idx_{table_name}_org_id
            ON "{table_name}"(organization_id);
        """
    )


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS scales (
            id BIGSERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            organization_id BIGINT NOT NULL REFERENCES organizations(id),
            scale_db_id VARCHAR(255),
            scale_name VARCHAR(255) NOT NULL,
            scale_pui VARCHAR(255),
            data_type VARCHAR(50),
            decimal_places INTEGER,
            valid_values_min INTEGER,
            valid_values_max INTEGER,
            valid_values_categories JSONB,
            ontology_db_id VARCHAR(255),
            ontology_name VARCHAR(255),
            ontology_version VARCHAR(50),
            additional_info JSONB,
            external_references JSONB
        );
        CREATE UNIQUE INDEX IF NOT EXISTS ix_scales_scale_db_id
            ON scales(scale_db_id);
        CREATE INDEX IF NOT EXISTS ix_scales_scale_name
            ON scales(scale_name);
        CREATE INDEX IF NOT EXISTS ix_scales_organization_id
            ON scales(organization_id);
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS methods (
            id BIGSERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            organization_id BIGINT NOT NULL REFERENCES organizations(id),
            method_db_id VARCHAR(255),
            method_name VARCHAR(255) NOT NULL,
            method_pui VARCHAR(255),
            method_class VARCHAR(100),
            description TEXT,
            formula TEXT,
            reference TEXT,
            bibliographical_reference TEXT,
            ontology_db_id VARCHAR(255),
            ontology_name VARCHAR(255),
            ontology_version VARCHAR(50),
            additional_info JSONB,
            external_references JSONB
        );
        CREATE UNIQUE INDEX IF NOT EXISTS ix_methods_method_db_id
            ON methods(method_db_id);
        CREATE INDEX IF NOT EXISTS ix_methods_method_name
            ON methods(method_name);
        CREATE INDEX IF NOT EXISTS ix_methods_organization_id
            ON methods(organization_id);
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS observation_levels (
            id BIGSERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            organization_id BIGINT NOT NULL REFERENCES organizations(id),
            level_name VARCHAR(100) NOT NULL,
            level_code VARCHAR(50),
            level_order INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_observation_levels_level_name
            ON observation_levels(level_name);
        CREATE INDEX IF NOT EXISTS ix_observation_levels_organization_id
            ON observation_levels(organization_id);
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS traits (
            id BIGSERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            organization_id BIGINT NOT NULL REFERENCES organizations(id),
            trait_db_id VARCHAR(255),
            trait_name VARCHAR(255) NOT NULL,
            trait_pui VARCHAR(255),
            trait_description TEXT,
            trait_class VARCHAR(100),
            synonyms JSONB,
            alternative_abbreviations JSONB,
            main_abbreviation VARCHAR(50),
            ontology_db_id VARCHAR(255),
            ontology_name VARCHAR(255),
            entity VARCHAR(255),
            attribute VARCHAR(255),
            status VARCHAR(50),
            additional_info JSONB,
            external_references JSONB
        );
        CREATE UNIQUE INDEX IF NOT EXISTS ix_traits_trait_db_id
            ON traits(trait_db_id);
        CREATE INDEX IF NOT EXISTS ix_traits_trait_name
            ON traits(trait_name);
        CREATE INDEX IF NOT EXISTS ix_traits_organization_id
            ON traits(organization_id);
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS germplasm_attribute_definitions (
            id BIGSERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            organization_id BIGINT NOT NULL REFERENCES organizations(id),
            attribute_db_id VARCHAR(255),
            attribute_name VARCHAR(255) NOT NULL,
            attribute_pui VARCHAR(255),
            attribute_description TEXT,
            attribute_category VARCHAR(100),
            common_crop_name VARCHAR(100),
            context_of_use JSONB,
            default_value VARCHAR(255),
            documentation_url TEXT,
            growth_stage VARCHAR(100),
            institution VARCHAR(255),
            language VARCHAR(10),
            scientist VARCHAR(255),
            status VARCHAR(50),
            submission_timestamp VARCHAR(50),
            synonyms JSONB,
            trait_db_id VARCHAR(255),
            trait_name VARCHAR(255),
            trait_description TEXT,
            trait_class VARCHAR(100),
            method_db_id VARCHAR(255),
            method_name VARCHAR(255),
            method_description TEXT,
            method_class VARCHAR(100),
            scale_db_id VARCHAR(255),
            scale_name VARCHAR(255),
            data_type VARCHAR(50),
            additional_info JSONB,
            external_references JSONB
        );
        CREATE UNIQUE INDEX IF NOT EXISTS ix_germplasm_attribute_definitions_attribute_db_id
            ON germplasm_attribute_definitions(attribute_db_id);
        CREATE INDEX IF NOT EXISTS ix_germplasm_attribute_definitions_attribute_name
            ON germplasm_attribute_definitions(attribute_name);
        CREATE INDEX IF NOT EXISTS ix_germplasm_attribute_definitions_attribute_category
            ON germplasm_attribute_definitions(attribute_category);
        CREATE INDEX IF NOT EXISTS ix_germplasm_attribute_definitions_organization_id
            ON germplasm_attribute_definitions(organization_id);
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS germplasm_attribute_values (
            id BIGSERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            organization_id BIGINT NOT NULL REFERENCES organizations(id),
            germplasm_id BIGINT NOT NULL REFERENCES germplasm(id),
            attribute_definition_id BIGINT REFERENCES germplasm_attribute_definitions(id),
            attribute_value_db_id VARCHAR(255),
            attribute_db_id VARCHAR(255),
            attribute_name VARCHAR(255),
            germplasm_db_id VARCHAR(255),
            germplasm_name VARCHAR(255),
            value TEXT NOT NULL,
            determined_date VARCHAR(50),
            additional_info JSONB,
            external_references JSONB
        );
        CREATE UNIQUE INDEX IF NOT EXISTS ix_germplasm_attribute_values_attribute_value_db_id
            ON germplasm_attribute_values(attribute_value_db_id);
        CREATE INDEX IF NOT EXISTS ix_germplasm_attribute_values_attribute_db_id
            ON germplasm_attribute_values(attribute_db_id);
        CREATE INDEX IF NOT EXISTS ix_germplasm_attribute_values_germplasm_id
            ON germplasm_attribute_values(germplasm_id);
        CREATE INDEX IF NOT EXISTS ix_germplasm_attribute_values_organization_id
            ON germplasm_attribute_values(organization_id);
        """
    )

    for table_name in REFERENCE_TABLES:
        _enable_tenant_rls(table_name)


def downgrade() -> None:
    for table_name in reversed(REFERENCE_TABLES):
        op.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
