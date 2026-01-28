"""Add BrAPI Core tables (Season, Ontology, List)

Revision ID: 012_brapi_core
Revises: 011_genotyping_tables
Create Date: 2025-12-23
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '012_brapi_core'
down_revision = '011_genotyping_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create seasons table
    op.create_table(
        'seasons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('season_db_id', sa.String(255), nullable=True),
        sa.Column('season_name', sa.String(255), nullable=False),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('additional_info', sa.JSON(), nullable=True),
        sa.Column('external_references', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_seasons_season_db_id', 'seasons', ['season_db_id'], unique=True)
    op.create_index('ix_seasons_season_name', 'seasons', ['season_name'])
    op.create_index('ix_seasons_year', 'seasons', ['year'])
    op.create_index('ix_seasons_organization_id', 'seasons', ['organization_id'])

    # Create ontologies table
    op.create_table(
        'ontologies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('ontology_db_id', sa.String(255), nullable=True),
        sa.Column('ontology_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('authors', sa.String(500), nullable=True),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('copyright', sa.String(500), nullable=True),
        sa.Column('licence', sa.String(255), nullable=True),
        sa.Column('documentation_url', sa.String(500), nullable=True),
        sa.Column('additional_info', sa.JSON(), nullable=True),
        sa.Column('external_references', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ontologies_ontology_db_id', 'ontologies', ['ontology_db_id'], unique=True)
    op.create_index('ix_ontologies_ontology_name', 'ontologies', ['ontology_name'])
    op.create_index('ix_ontologies_organization_id', 'ontologies', ['organization_id'])

    # Create lists table
    op.create_table(
        'lists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('list_db_id', sa.String(255), nullable=True),
        sa.Column('list_name', sa.String(255), nullable=False),
        sa.Column('list_description', sa.Text(), nullable=True),
        sa.Column('list_type', sa.String(100), nullable=True),
        sa.Column('list_size', sa.Integer(), default=0),
        sa.Column('list_source', sa.String(255), nullable=True),
        sa.Column('list_owner_name', sa.String(255), nullable=True),
        sa.Column('list_owner_person_db_id', sa.String(255), nullable=True),
        sa.Column('date_created', sa.String(50), nullable=True),
        sa.Column('date_modified', sa.String(50), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('additional_info', sa.JSON(), nullable=True),
        sa.Column('external_references', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lists_list_db_id', 'lists', ['list_db_id'], unique=True)
    op.create_index('ix_lists_list_name', 'lists', ['list_name'])
    op.create_index('ix_lists_list_type', 'lists', ['list_type'])
    op.create_index('ix_lists_organization_id', 'lists', ['organization_id'])


def downgrade() -> None:
    op.drop_table('lists')
    op.drop_table('ontologies')
    op.drop_table('seasons')
