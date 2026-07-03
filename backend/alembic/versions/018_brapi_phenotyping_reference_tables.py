"""BrAPI Phenotyping Reference Tables

Creates tables for:
- scales: Measurement scales
- methods: Measurement methods
- observation_levels: Hierarchical observation levels
- traits: Trait definitions
- germplasm_attribute_definitions: Attribute type definitions
- germplasm_attribute_values: Attribute values for germplasm

Revision ID: 018
Revises: 017_workspace_preferences
Create Date: 2025-12-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Scales table
    op.create_table(
        'scales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('scale_db_id', sa.String(255), nullable=True),
        sa.Column('scale_name', sa.String(255), nullable=False),
        sa.Column('scale_pui', sa.String(255), nullable=True),
        sa.Column('data_type', sa.String(50), nullable=True),
        sa.Column('decimal_places', sa.Integer(), nullable=True),
        sa.Column('valid_values_min', sa.Integer(), nullable=True),
        sa.Column('valid_values_max', sa.Integer(), nullable=True),
        sa.Column('valid_values_categories', sa.JSON(), nullable=True),
        sa.Column('ontology_db_id', sa.String(255), nullable=True),
        sa.Column('ontology_name', sa.String(255), nullable=True),
        sa.Column('ontology_version', sa.String(50), nullable=True),
        sa.Column('additional_info', sa.JSON(), nullable=True),
        sa.Column('external_references', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scales_organization_id', 'scales', ['organization_id'])
    op.create_index('ix_scales_scale_db_id', 'scales', ['scale_db_id'], unique=True)
    op.create_index('ix_scales_scale_name', 'scales', ['scale_name'])
    
    # Methods table
    op.create_table(
        'methods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('method_db_id', sa.String(255), nullable=True),
        sa.Column('method_name', sa.String(255), nullable=False),
        sa.Column('method_pui', sa.String(255), nullable=True),
        sa.Column('method_class', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('formula', sa.Text(), nullable=True),
        sa.Column('reference', sa.Text(), nullable=True),
        sa.Column('bibliographical_reference', sa.Text(), nullable=True),
        sa.Column('ontology_db_id', sa.String(255), nullable=True),
        sa.Column('ontology_name', sa.String(255), nullable=True),
        sa.Column('ontology_version', sa.String(50), nullable=True),
        sa.Column('additional_info', sa.JSON(), nullable=True),
        sa.Column('external_references', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_methods_organization_id', 'methods', ['organization_id'])
    op.create_index('ix_methods_method_db_id', 'methods', ['method_db_id'], unique=True)
    op.create_index('ix_methods_method_name', 'methods', ['method_name'])
    
    # Observation Levels table
    op.create_table(
        'observation_levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('level_name', sa.String(100), nullable=False),
        sa.Column('level_code', sa.String(50), nullable=True),
        sa.Column('level_order', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_observation_levels_organization_id', 'observation_levels', ['organization_id'])
    op.create_index('ix_observation_levels_level_name', 'observation_levels', ['level_name'])
    
    # Traits table
    op.create_table(
        'traits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('trait_db_id', sa.String(255), nullable=True),
        sa.Column('trait_name', sa.String(255), nullable=False),
        sa.Column('trait_pui', sa.String(255), nullable=True),
        sa.Column('trait_description', sa.Text(), nullable=True),
        sa.Column('trait_class', sa.String(100), nullable=True),
        sa.Column('synonyms', sa.JSON(), nullable=True),
        sa.Column('alternative_abbreviations', sa.JSON(), nullable=True),
        sa.Column('main_abbreviation', sa.String(50), nullable=True),
        sa.Column('ontology_db_id', sa.String(255), nullable=True),
        sa.Column('ontology_name', sa.String(255), nullable=True),
        sa.Column('entity', sa.String(255), nullable=True),
        sa.Column('attribute', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('additional_info', sa.JSON(), nullable=True),
        sa.Column('external_references', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_traits_organization_id', 'traits', ['organization_id'])
    op.create_index('ix_traits_trait_db_id', 'traits', ['trait_db_id'], unique=True)
    op.create_index('ix_traits_trait_name', 'traits', ['trait_name'])
    
    # Germplasm Attribute Definitions table
    op.create_table(
        'germplasm_attribute_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('attribute_db_id', sa.String(255), nullable=True),
        sa.Column('attribute_name', sa.String(255), nullable=False),
        sa.Column('attribute_pui', sa.String(255), nullable=True),
        sa.Column('attribute_description', sa.Text(), nullable=True),
        sa.Column('attribute_category', sa.String(100), nullable=True),
        sa.Column('common_crop_name', sa.String(100), nullable=True),
        sa.Column('context_of_use', sa.JSON(), nullable=True),
        sa.Column('default_value', sa.String(255), nullable=True),
        sa.Column('documentation_url', sa.Text(), nullable=True),
        sa.Column('growth_stage', sa.String(100), nullable=True),
        sa.Column('institution', sa.String(255), nullable=True),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('scientist', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('submission_timestamp', sa.String(50), nullable=True),
        sa.Column('synonyms', sa.JSON(), nullable=True),
        sa.Column('trait_db_id', sa.String(255), nullable=True),
        sa.Column('trait_name', sa.String(255), nullable=True),
        sa.Column('trait_description', sa.Text(), nullable=True),
        sa.Column('trait_class', sa.String(100), nullable=True),
        sa.Column('method_db_id', sa.String(255), nullable=True),
        sa.Column('method_name', sa.String(255), nullable=True),
        sa.Column('method_description', sa.Text(), nullable=True),
        sa.Column('method_class', sa.String(100), nullable=True),
        sa.Column('scale_db_id', sa.String(255), nullable=True),
        sa.Column('scale_name', sa.String(255), nullable=True),
        sa.Column('data_type', sa.String(50), nullable=True),
        sa.Column('additional_info', sa.JSON(), nullable=True),
        sa.Column('external_references', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_germplasm_attribute_definitions_organization_id', 'germplasm_attribute_definitions', ['organization_id'])
    op.create_index('ix_germplasm_attribute_definitions_attribute_db_id', 'germplasm_attribute_definitions', ['attribute_db_id'], unique=True)
    op.create_index('ix_germplasm_attribute_definitions_attribute_name', 'germplasm_attribute_definitions', ['attribute_name'])
    op.create_index('ix_germplasm_attribute_definitions_attribute_category', 'germplasm_attribute_definitions', ['attribute_category'])
    
    # Germplasm Attribute Values table
    op.create_table(
        'germplasm_attribute_values',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('germplasm_id', sa.Integer(), nullable=False),
        sa.Column('attribute_definition_id', sa.Integer(), nullable=True),
        sa.Column('attribute_value_db_id', sa.String(255), nullable=True),
        sa.Column('attribute_db_id', sa.String(255), nullable=True),
        sa.Column('attribute_name', sa.String(255), nullable=True),
        sa.Column('germplasm_db_id', sa.String(255), nullable=True),
        sa.Column('germplasm_name', sa.String(255), nullable=True),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('determined_date', sa.String(50), nullable=True),
        sa.Column('additional_info', sa.JSON(), nullable=True),
        sa.Column('external_references', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['germplasm_id'], ['germplasm.id']),
        sa.ForeignKeyConstraint(['attribute_definition_id'], ['germplasm_attribute_definitions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_germplasm_attribute_values_organization_id', 'germplasm_attribute_values', ['organization_id'])
    op.create_index('ix_germplasm_attribute_values_germplasm_id', 'germplasm_attribute_values', ['germplasm_id'])
    op.create_index('ix_germplasm_attribute_values_attribute_value_db_id', 'germplasm_attribute_values', ['attribute_value_db_id'], unique=True)
    op.create_index('ix_germplasm_attribute_values_attribute_db_id', 'germplasm_attribute_values', ['attribute_db_id'])


def downgrade() -> None:
    op.drop_table('germplasm_attribute_values')
    op.drop_table('germplasm_attribute_definitions')
    op.drop_table('traits')
    op.drop_table('observation_levels')
    op.drop_table('methods')
    op.drop_table('scales')
