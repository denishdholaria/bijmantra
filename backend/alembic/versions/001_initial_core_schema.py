"""Initial core schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_index(op.f('ix_organizations_name'), 'organizations', ['name'], unique=True)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_organization_id'), 'users', ['organization_id'], unique=False)
    
    # Create people table
    op.create_table(
        'people',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('person_db_id', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('middle_name', sa.String(length=100), nullable=True),
        sa.Column('email_address', sa.String(length=255), nullable=True),
        sa.Column('phone_number', sa.String(length=50), nullable=True),
        sa.Column('mailing_address', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_people_id'), 'people', ['id'], unique=False)
    op.create_index(op.f('ix_people_person_db_id'), 'people', ['person_db_id'], unique=True)
    
    # Create programs table
    op.create_table(
        'programs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('program_db_id', sa.String(length=255), nullable=True),
        sa.Column('program_name', sa.String(length=255), nullable=False),
        sa.Column('abbreviation', sa.String(length=50), nullable=True),
        sa.Column('objective', sa.Text(), nullable=True),
        sa.Column('lead_person_db_id', sa.Integer(), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['lead_person_db_id'], ['people.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_programs_id'), 'programs', ['id'], unique=False)
    op.create_index(op.f('ix_programs_program_db_id'), 'programs', ['program_db_id'], unique=True)
    op.create_index(op.f('ix_programs_program_name'), 'programs', ['program_name'], unique=False)
    op.create_index(op.f('ix_programs_organization_id'), 'programs', ['organization_id'], unique=False)
    
    # Create locations table
    op.create_table(
        'locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('location_db_id', sa.String(length=255), nullable=True),
        sa.Column('location_name', sa.String(length=255), nullable=False),
        sa.Column('location_type', sa.String(length=50), nullable=True),
        sa.Column('abbreviation', sa.String(length=50), nullable=True),
        sa.Column('country_name', sa.String(length=100), nullable=True),
        sa.Column('country_code', sa.String(length=3), nullable=True),
        sa.Column('institute_name', sa.String(length=255), nullable=True),
        sa.Column('institute_address', sa.Text(), nullable=True),
        sa.Column('coordinates', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
        sa.Column('coordinate_uncertainty', sa.String(length=50), nullable=True),
        sa.Column('coordinate_description', sa.Text(), nullable=True),
        sa.Column('altitude', sa.String(length=50), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_locations_id'), 'locations', ['id'], unique=False)
    op.create_index(op.f('ix_locations_location_db_id'), 'locations', ['location_db_id'], unique=True)
    op.create_index(op.f('ix_locations_location_name'), 'locations', ['location_name'], unique=False)
    # GeoAlchemy2 may auto-create this index, so use raw SQL with IF NOT EXISTS
    op.execute('CREATE INDEX IF NOT EXISTS idx_locations_coordinates ON locations USING gist (coordinates)')
    
    # Create trials table
    op.create_table(
        'trials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('trial_db_id', sa.String(length=255), nullable=True),
        sa.Column('trial_name', sa.String(length=255), nullable=False),
        sa.Column('trial_description', sa.Text(), nullable=True),
        sa.Column('trial_type', sa.String(length=100), nullable=True),
        sa.Column('start_date', sa.String(length=50), nullable=True),
        sa.Column('end_date', sa.String(length=50), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('common_crop_name', sa.String(length=100), nullable=True),
        sa.Column('document_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trials_id'), 'trials', ['id'], unique=False)
    op.create_index(op.f('ix_trials_trial_db_id'), 'trials', ['trial_db_id'], unique=True)
    op.create_index(op.f('ix_trials_trial_name'), 'trials', ['trial_name'], unique=False)
    op.create_index(op.f('ix_trials_program_id'), 'trials', ['program_id'], unique=False)
    op.create_index(op.f('ix_trials_organization_id'), 'trials', ['organization_id'], unique=False)
    
    # Create studies table
    op.create_table(
        'studies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('trial_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('study_db_id', sa.String(length=255), nullable=True),
        sa.Column('study_name', sa.String(length=255), nullable=False),
        sa.Column('study_description', sa.Text(), nullable=True),
        sa.Column('study_type', sa.String(length=100), nullable=True),
        sa.Column('study_code', sa.String(length=100), nullable=True),
        sa.Column('start_date', sa.String(length=50), nullable=True),
        sa.Column('end_date', sa.String(length=50), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('common_crop_name', sa.String(length=100), nullable=True),
        sa.Column('cultural_practices', sa.Text(), nullable=True),
        sa.Column('observation_levels', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('observation_units_description', sa.Text(), nullable=True),
        sa.Column('license', sa.String(length=255), nullable=True),
        sa.Column('data_links', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['trial_id'], ['trials.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_studies_id'), 'studies', ['id'], unique=False)
    op.create_index(op.f('ix_studies_study_db_id'), 'studies', ['study_db_id'], unique=True)
    op.create_index(op.f('ix_studies_study_name'), 'studies', ['study_name'], unique=False)
    op.create_index(op.f('ix_studies_trial_id'), 'studies', ['trial_id'], unique=False)
    op.create_index(op.f('ix_studies_organization_id'), 'studies', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_table('studies')
    op.drop_table('trials')
    op.drop_table('locations')
    op.drop_table('programs')
    op.drop_table('people')
    op.drop_table('users')
    op.drop_table('organizations')
    op.execute('DROP EXTENSION IF EXISTS postgis')
