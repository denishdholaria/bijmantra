"""Germplasm tables for BrAPI

Revision ID: 009
Revises: 008
Create Date: 2025-12-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create germplasm table
    op.create_table(
        'germplasm',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('germplasm_db_id', sa.String(length=255), nullable=True),
        sa.Column('germplasm_pui', sa.String(length=255), nullable=True),
        sa.Column('germplasm_name', sa.String(length=255), nullable=False),
        sa.Column('default_display_name', sa.String(length=255), nullable=True),
        sa.Column('accession_number', sa.String(length=255), nullable=True),
        sa.Column('common_crop_name', sa.String(length=100), nullable=True),
        sa.Column('genus', sa.String(length=100), nullable=True),
        sa.Column('species', sa.String(length=255), nullable=True),
        sa.Column('species_authority', sa.String(length=255), nullable=True),
        sa.Column('subtaxa', sa.String(length=255), nullable=True),
        sa.Column('subtaxa_authority', sa.String(length=255), nullable=True),
        sa.Column('country_of_origin_code', sa.String(length=3), nullable=True),
        sa.Column('institute_code', sa.String(length=50), nullable=True),
        sa.Column('institute_name', sa.String(length=255), nullable=True),
        sa.Column('biological_status_of_accession_code', sa.String(length=10), nullable=True),
        sa.Column('biological_status_of_accession_description', sa.String(length=255), nullable=True),
        sa.Column('pedigree', sa.Text(), nullable=True),
        sa.Column('breeding_method_db_id', sa.String(length=255), nullable=True),
        sa.Column('seed_source', sa.String(length=255), nullable=True),
        sa.Column('seed_source_description', sa.Text(), nullable=True),
        sa.Column('acquisition_date', sa.Date(), nullable=True),
        sa.Column('acquisition_source_code', sa.String(length=10), nullable=True),
        sa.Column('collection_date', sa.Date(), nullable=True),
        sa.Column('collection_site', sa.Text(), nullable=True),
        sa.Column('storage_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('synonyms', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('donors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_germplasm_id', 'germplasm', ['id'], unique=False)
    op.create_index('ix_germplasm_germplasm_db_id', 'germplasm', ['germplasm_db_id'], unique=True)
    op.create_index('ix_germplasm_germplasm_pui', 'germplasm', ['germplasm_pui'], unique=False)
    op.create_index('ix_germplasm_germplasm_name', 'germplasm', ['germplasm_name'], unique=False)
    op.create_index('ix_germplasm_accession_number', 'germplasm', ['accession_number'], unique=False)
    op.create_index('ix_germplasm_common_crop_name', 'germplasm', ['common_crop_name'], unique=False)
    op.create_index('ix_germplasm_genus', 'germplasm', ['genus'], unique=False)
    op.create_index('ix_germplasm_organization_id', 'germplasm', ['organization_id'], unique=False)
    
    # Create germplasm_attributes table
    op.create_table(
        'germplasm_attributes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('germplasm_id', sa.Integer(), nullable=False),
        sa.Column('attribute_db_id', sa.String(length=255), nullable=True),
        sa.Column('attribute_name', sa.String(length=255), nullable=False),
        sa.Column('attribute_category', sa.String(length=100), nullable=True),
        sa.Column('attribute_description', sa.Text(), nullable=True),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('determination_date', sa.Date(), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['germplasm_id'], ['germplasm.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_germplasm_attributes_id', 'germplasm_attributes', ['id'], unique=False)
    op.create_index('ix_germplasm_attributes_germplasm_id', 'germplasm_attributes', ['germplasm_id'], unique=False)
    op.create_index('ix_germplasm_attributes_attribute_db_id', 'germplasm_attributes', ['attribute_db_id'], unique=False)
    op.create_index('ix_germplasm_attributes_organization_id', 'germplasm_attributes', ['organization_id'], unique=False)
    
    # Create crossing_projects table
    op.create_table(
        'crossing_projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=True),
        sa.Column('crossing_project_db_id', sa.String(length=255), nullable=True),
        sa.Column('crossing_project_name', sa.String(length=255), nullable=False),
        sa.Column('crossing_project_description', sa.Text(), nullable=True),
        sa.Column('common_crop_name', sa.String(length=100), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_crossing_projects_id', 'crossing_projects', ['id'], unique=False)
    op.create_index('ix_crossing_projects_crossing_project_db_id', 'crossing_projects', ['crossing_project_db_id'], unique=True)
    op.create_index('ix_crossing_projects_organization_id', 'crossing_projects', ['organization_id'], unique=False)
    op.create_index('ix_crossing_projects_program_id', 'crossing_projects', ['program_id'], unique=False)
    
    # Create crosses table
    op.create_table(
        'crosses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('crossing_project_id', sa.Integer(), nullable=True),
        sa.Column('cross_db_id', sa.String(length=255), nullable=True),
        sa.Column('cross_name', sa.String(length=255), nullable=False),
        sa.Column('cross_type', sa.String(length=50), nullable=True),
        sa.Column('parent1_db_id', sa.Integer(), nullable=True),
        sa.Column('parent1_type', sa.String(length=20), nullable=True),
        sa.Column('parent2_db_id', sa.Integer(), nullable=True),
        sa.Column('parent2_type', sa.String(length=20), nullable=True),
        sa.Column('crossing_year', sa.Integer(), nullable=True),
        sa.Column('pollination_time_stamp', sa.String(length=50), nullable=True),
        sa.Column('cross_status', sa.String(length=50), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['crossing_project_id'], ['crossing_projects.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['parent1_db_id'], ['germplasm.id'], ),
        sa.ForeignKeyConstraint(['parent2_db_id'], ['germplasm.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_crosses_id', 'crosses', ['id'], unique=False)
    op.create_index('ix_crosses_cross_db_id', 'crosses', ['cross_db_id'], unique=True)
    op.create_index('ix_crosses_organization_id', 'crosses', ['organization_id'], unique=False)
    op.create_index('ix_crosses_crossing_project_id', 'crosses', ['crossing_project_id'], unique=False)
    
    # Create planned_crosses table
    op.create_table(
        'planned_crosses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('crossing_project_id', sa.Integer(), nullable=True),
        sa.Column('planned_cross_db_id', sa.String(length=255), nullable=True),
        sa.Column('planned_cross_name', sa.String(length=255), nullable=True),
        sa.Column('cross_type', sa.String(length=50), nullable=True),
        sa.Column('parent1_db_id', sa.Integer(), nullable=True),
        sa.Column('parent1_type', sa.String(length=20), nullable=True),
        sa.Column('parent2_db_id', sa.Integer(), nullable=True),
        sa.Column('parent2_type', sa.String(length=20), nullable=True),
        sa.Column('number_of_progeny', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['crossing_project_id'], ['crossing_projects.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['parent1_db_id'], ['germplasm.id'], ),
        sa.ForeignKeyConstraint(['parent2_db_id'], ['germplasm.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_planned_crosses_id', 'planned_crosses', ['id'], unique=False)
    op.create_index('ix_planned_crosses_planned_cross_db_id', 'planned_crosses', ['planned_cross_db_id'], unique=True)
    op.create_index('ix_planned_crosses_organization_id', 'planned_crosses', ['organization_id'], unique=False)
    op.create_index('ix_planned_crosses_crossing_project_id', 'planned_crosses', ['crossing_project_id'], unique=False)
    
    # Create seedlots table
    op.create_table(
        'seedlots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('germplasm_id', sa.Integer(), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('program_id', sa.Integer(), nullable=True),
        sa.Column('seedlot_db_id', sa.String(length=255), nullable=True),
        sa.Column('seedlot_name', sa.String(length=255), nullable=False),
        sa.Column('seedlot_description', sa.Text(), nullable=True),
        sa.Column('source_collection', sa.String(length=255), nullable=True),
        sa.Column('storage_location', sa.String(length=255), nullable=True),
        sa.Column('count', sa.Integer(), nullable=True),
        sa.Column('units', sa.String(length=50), nullable=True),
        sa.Column('creation_date', sa.Date(), nullable=True),
        sa.Column('last_updated', sa.Date(), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['germplasm_id'], ['germplasm.id'], ),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_seedlots_id', 'seedlots', ['id'], unique=False)
    op.create_index('ix_seedlots_seedlot_db_id', 'seedlots', ['seedlot_db_id'], unique=True)
    op.create_index('ix_seedlots_organization_id', 'seedlots', ['organization_id'], unique=False)
    op.create_index('ix_seedlots_germplasm_id', 'seedlots', ['germplasm_id'], unique=False)
    op.create_index('ix_seedlots_location_id', 'seedlots', ['location_id'], unique=False)
    op.create_index('ix_seedlots_program_id', 'seedlots', ['program_id'], unique=False)
    
    # Create seedlot_transactions table
    op.create_table(
        'seedlot_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('seedlot_id', sa.Integer(), nullable=False),
        sa.Column('transaction_db_id', sa.String(length=255), nullable=True),
        sa.Column('transaction_description', sa.Text(), nullable=True),
        sa.Column('transaction_timestamp', sa.String(length=50), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('units', sa.String(length=50), nullable=True),
        sa.Column('from_seedlot_db_id', sa.String(length=255), nullable=True),
        sa.Column('to_seedlot_db_id', sa.String(length=255), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['seedlot_id'], ['seedlots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_seedlot_transactions_id', 'seedlot_transactions', ['id'], unique=False)
    op.create_index('ix_seedlot_transactions_transaction_db_id', 'seedlot_transactions', ['transaction_db_id'], unique=True)
    op.create_index('ix_seedlot_transactions_organization_id', 'seedlot_transactions', ['organization_id'], unique=False)
    op.create_index('ix_seedlot_transactions_seedlot_id', 'seedlot_transactions', ['seedlot_id'], unique=False)
    
    # Create breeding_methods table
    op.create_table(
        'breeding_methods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('breeding_method_db_id', sa.String(length=255), nullable=True),
        sa.Column('breeding_method_name', sa.String(length=255), nullable=False),
        sa.Column('abbreviation', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_breeding_methods_id', 'breeding_methods', ['id'], unique=False)
    op.create_index('ix_breeding_methods_breeding_method_db_id', 'breeding_methods', ['breeding_method_db_id'], unique=True)
    op.create_index('ix_breeding_methods_organization_id', 'breeding_methods', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_table('breeding_methods')
    op.drop_table('seedlot_transactions')
    op.drop_table('seedlots')
    op.drop_table('planned_crosses')
    op.drop_table('crosses')
    op.drop_table('crossing_projects')
    op.drop_table('germplasm_attributes')
    op.drop_table('germplasm')
