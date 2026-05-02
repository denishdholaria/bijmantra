"""Phenotyping tables for BrAPI

Revision ID: 010
Revises: 009
Create Date: 2025-12-23

Tables for:
- observation_variables (traits)
- observations
- observation_units
- samples
- images
- events
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create observation_variables (traits) table
    op.create_table(
        'observation_variables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('observation_variable_db_id', sa.String(length=255), nullable=True),
        sa.Column('observation_variable_name', sa.String(length=255), nullable=False),
        sa.Column('common_crop_name', sa.String(length=100), nullable=True),
        sa.Column('default_value', sa.String(length=255), nullable=True),
        sa.Column('document_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('growth_stage', sa.String(length=100), nullable=True),
        sa.Column('institution', sa.String(length=255), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('scientist', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('submission_timestamp', sa.String(length=50), nullable=True),
        sa.Column('synonyms', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        # Trait info
        sa.Column('trait_db_id', sa.String(length=255), nullable=True),
        sa.Column('trait_name', sa.String(length=255), nullable=True),
        sa.Column('trait_description', sa.Text(), nullable=True),
        sa.Column('trait_class', sa.String(length=100), nullable=True),
        # Method info
        sa.Column('method_db_id', sa.String(length=255), nullable=True),
        sa.Column('method_name', sa.String(length=255), nullable=True),
        sa.Column('method_description', sa.Text(), nullable=True),
        sa.Column('method_class', sa.String(length=100), nullable=True),
        sa.Column('formula', sa.Text(), nullable=True),
        # Scale info
        sa.Column('scale_db_id', sa.String(length=255), nullable=True),
        sa.Column('scale_name', sa.String(length=255), nullable=True),
        sa.Column('data_type', sa.String(length=50), nullable=True),
        sa.Column('decimal_places', sa.Integer(), nullable=True),
        sa.Column('valid_values', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        # Ontology
        sa.Column('ontology_db_id', sa.String(length=255), nullable=True),
        sa.Column('ontology_name', sa.String(length=255), nullable=True),
        # BrAPI additional info
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_observation_variables_id', 'observation_variables', ['id'], unique=False)
    op.create_index('ix_observation_variables_db_id', 'observation_variables', ['observation_variable_db_id'], unique=True)
    op.create_index('ix_observation_variables_name', 'observation_variables', ['observation_variable_name'], unique=False)
    op.create_index('ix_observation_variables_org_id', 'observation_variables', ['organization_id'], unique=False)
    op.create_index('ix_observation_variables_trait_db_id', 'observation_variables', ['trait_db_id'], unique=False)

    # Create observation_units table
    op.create_table(
        'observation_units',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('study_id', sa.Integer(), nullable=True),
        sa.Column('germplasm_id', sa.Integer(), nullable=True),
        sa.Column('observation_unit_db_id', sa.String(length=255), nullable=True),
        sa.Column('observation_unit_name', sa.String(length=255), nullable=False),
        sa.Column('observation_unit_pui', sa.String(length=255), nullable=True),
        sa.Column('cross_db_id', sa.String(length=255), nullable=True),
        sa.Column('seedlot_db_id', sa.String(length=255), nullable=True),
        sa.Column('observation_level', sa.String(length=50), nullable=True),
        sa.Column('observation_level_code', sa.String(length=50), nullable=True),
        sa.Column('observation_level_order', sa.Integer(), nullable=True),
        # Position info
        sa.Column('position_coordinate_x', sa.String(length=50), nullable=True),
        sa.Column('position_coordinate_x_type', sa.String(length=50), nullable=True),
        sa.Column('position_coordinate_y', sa.String(length=50), nullable=True),
        sa.Column('position_coordinate_y_type', sa.String(length=50), nullable=True),
        sa.Column('entry_type', sa.String(length=50), nullable=True),
        sa.Column('geo_coordinates', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        # Treatments
        sa.Column('treatments', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        # BrAPI additional info
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ),
        sa.ForeignKeyConstraint(['germplasm_id'], ['germplasm.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_observation_units_id', 'observation_units', ['id'], unique=False)
    op.create_index('ix_observation_units_db_id', 'observation_units', ['observation_unit_db_id'], unique=True)
    op.create_index('ix_observation_units_name', 'observation_units', ['observation_unit_name'], unique=False)
    op.create_index('ix_observation_units_org_id', 'observation_units', ['organization_id'], unique=False)
    op.create_index('ix_observation_units_study_id', 'observation_units', ['study_id'], unique=False)
    op.create_index('ix_observation_units_germplasm_id', 'observation_units', ['germplasm_id'], unique=False)

    # Create observations table
    op.create_table(
        'observations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('observation_unit_id', sa.Integer(), nullable=True),
        sa.Column('observation_variable_id', sa.Integer(), nullable=True),
        sa.Column('study_id', sa.Integer(), nullable=True),
        sa.Column('germplasm_id', sa.Integer(), nullable=True),
        sa.Column('observation_db_id', sa.String(length=255), nullable=True),
        sa.Column('collector', sa.String(length=255), nullable=True),
        sa.Column('observation_time_stamp', sa.String(length=50), nullable=True),
        sa.Column('season_db_id', sa.String(length=255), nullable=True),
        sa.Column('upload_timestamp', sa.String(length=50), nullable=True),
        sa.Column('value', sa.Text(), nullable=True),
        # Geo coordinates
        sa.Column('geo_coordinates', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        # BrAPI additional info
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['observation_unit_id'], ['observation_units.id'], ),
        sa.ForeignKeyConstraint(['observation_variable_id'], ['observation_variables.id'], ),
        sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ),
        sa.ForeignKeyConstraint(['germplasm_id'], ['germplasm.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_observations_id', 'observations', ['id'], unique=False)
    op.create_index('ix_observations_db_id', 'observations', ['observation_db_id'], unique=True)
    op.create_index('ix_observations_org_id', 'observations', ['organization_id'], unique=False)
    op.create_index('ix_observations_unit_id', 'observations', ['observation_unit_id'], unique=False)
    op.create_index('ix_observations_variable_id', 'observations', ['observation_variable_id'], unique=False)
    op.create_index('ix_observations_study_id', 'observations', ['study_id'], unique=False)

    # Create samples table
    op.create_table(
        'samples',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('observation_unit_id', sa.Integer(), nullable=True),
        sa.Column('germplasm_id', sa.Integer(), nullable=True),
        sa.Column('study_id', sa.Integer(), nullable=True),
        sa.Column('sample_db_id', sa.String(length=255), nullable=True),
        sa.Column('sample_name', sa.String(length=255), nullable=False),
        sa.Column('sample_pui', sa.String(length=255), nullable=True),
        sa.Column('sample_type', sa.String(length=100), nullable=True),
        sa.Column('sample_description', sa.Text(), nullable=True),
        sa.Column('sample_barcode', sa.String(length=255), nullable=True),
        sa.Column('sample_group_db_id', sa.String(length=255), nullable=True),
        sa.Column('sample_timestamp', sa.String(length=50), nullable=True),
        sa.Column('taken_by', sa.String(length=255), nullable=True),
        sa.Column('plate_db_id', sa.String(length=255), nullable=True),
        sa.Column('plate_name', sa.String(length=255), nullable=True),
        sa.Column('plate_index', sa.Integer(), nullable=True),
        sa.Column('well', sa.String(length=10), nullable=True),
        sa.Column('row', sa.String(length=10), nullable=True),
        sa.Column('column', sa.Integer(), nullable=True),
        sa.Column('tissue_type', sa.String(length=100), nullable=True),
        sa.Column('concentration', sa.Float(), nullable=True),
        sa.Column('volume', sa.Float(), nullable=True),
        # BrAPI additional info
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['observation_unit_id'], ['observation_units.id'], ),
        sa.ForeignKeyConstraint(['germplasm_id'], ['germplasm.id'], ),
        sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_samples_id', 'samples', ['id'], unique=False)
    op.create_index('ix_samples_db_id', 'samples', ['sample_db_id'], unique=True)
    op.create_index('ix_samples_name', 'samples', ['sample_name'], unique=False)
    op.create_index('ix_samples_org_id', 'samples', ['organization_id'], unique=False)
    op.create_index('ix_samples_observation_unit_id', 'samples', ['observation_unit_id'], unique=False)
    op.create_index('ix_samples_germplasm_id', 'samples', ['germplasm_id'], unique=False)
    op.create_index('ix_samples_plate_db_id', 'samples', ['plate_db_id'], unique=False)

    # Create images table
    op.create_table(
        'images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('observation_unit_id', sa.Integer(), nullable=True),
        sa.Column('observation_db_id', sa.String(length=255), nullable=True),
        sa.Column('image_db_id', sa.String(length=255), nullable=True),
        sa.Column('image_name', sa.String(length=255), nullable=False),
        sa.Column('image_file_name', sa.String(length=255), nullable=True),
        sa.Column('image_file_size', sa.Integer(), nullable=True),
        sa.Column('image_height', sa.Integer(), nullable=True),
        sa.Column('image_width', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('image_time_stamp', sa.String(length=50), nullable=True),
        sa.Column('copyright', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('descriptive_ontology_terms', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('image_location', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        # BrAPI additional info
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['observation_unit_id'], ['observation_units.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_images_id', 'images', ['id'], unique=False)
    op.create_index('ix_images_db_id', 'images', ['image_db_id'], unique=True)
    op.create_index('ix_images_name', 'images', ['image_name'], unique=False)
    op.create_index('ix_images_org_id', 'images', ['organization_id'], unique=False)
    op.create_index('ix_images_observation_unit_id', 'images', ['observation_unit_id'], unique=False)

    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('study_id', sa.Integer(), nullable=True),
        sa.Column('event_db_id', sa.String(length=255), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_type_db_id', sa.String(length=255), nullable=True),
        sa.Column('event_description', sa.Text(), nullable=True),
        sa.Column('date', sa.String(length=50), nullable=True),
        sa.Column('observation_unit_db_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('event_parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        # BrAPI additional info
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_events_id', 'events', ['id'], unique=False)
    op.create_index('ix_events_db_id', 'events', ['event_db_id'], unique=True)
    op.create_index('ix_events_type', 'events', ['event_type'], unique=False)
    op.create_index('ix_events_org_id', 'events', ['organization_id'], unique=False)
    op.create_index('ix_events_study_id', 'events', ['study_id'], unique=False)


def downgrade() -> None:
    op.drop_table('events')
    op.drop_table('images')
    op.drop_table('samples')
    op.drop_table('observations')
    op.drop_table('observation_units')
    op.drop_table('observation_variables')
