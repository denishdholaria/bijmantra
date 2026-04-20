"""Add stress resistance and field operations tables

Revision ID: 014
Revises: 013_user_management_tables
Create Date: 2025-12-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # CREATE ENUMS FIRST (using raw SQL for safety)
    # ============================================
    
    # Create stress category enum
    op.execute("DO $$ BEGIN CREATE TYPE stresscategory AS ENUM ('water', 'temperature', 'soil', 'radiation', 'nutrient', 'other'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create pathogen type enum
    op.execute("DO $$ BEGIN CREATE TYPE pathogentype AS ENUM ('bacteria', 'fungus', 'virus', 'insect', 'nematode', 'other'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create resistance type enum
    op.execute("DO $$ BEGIN CREATE TYPE resistancetype AS ENUM ('complete', 'partial', 'recessive', 'dominant', 'quantitative'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create batch status enum
    op.execute("DO $$ BEGIN CREATE TYPE batchstatus AS ENUM ('sowing', 'germinating', 'growing', 'ready', 'transplanted', 'failed'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # ============================================
    # ABIOTIC STRESS TABLES
    # ============================================
    
    op.create_table(
        'abiotic_stresses',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer, sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('stress_code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', postgresql.ENUM('water', 'temperature', 'soil', 'radiation', 'nutrient', 'other', name='stresscategory', create_type=False), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('screening_method', sa.String(255)),
        sa.Column('screening_stages', postgresql.ARRAY(sa.String)),
        sa.Column('screening_duration', sa.String(100)),
        sa.Column('indicators', postgresql.ARRAY(sa.String)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'stress_code', name='uq_abiotic_stress_code'),
    )
    op.create_index('ix_abiotic_stress_org_category', 'abiotic_stresses', ['organization_id', 'category'])
    
    op.create_table(
        'tolerance_genes',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer, sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('stress_id', sa.Integer, sa.ForeignKey('abiotic_stresses.id'), nullable=False),
        sa.Column('gene_code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('mechanism', sa.String(255)),
        sa.Column('crop', sa.String(100)),
        sa.Column('chromosome', sa.String(50)),
        sa.Column('position_start', sa.Integer),
        sa.Column('position_end', sa.Integer),
        sa.Column('markers', postgresql.ARRAY(sa.String)),
        sa.Column('source_germplasm', sa.String(255)),
        sa.Column('reference', sa.Text),
        sa.Column('is_validated', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'gene_code', name='uq_tolerance_gene_code'),
    )
    op.create_index('ix_tolerance_gene_org_crop', 'tolerance_genes', ['organization_id', 'crop'])
    
    # ============================================
    # DISEASE RESISTANCE TABLES
    # ============================================
    
    op.create_table(
        'diseases',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer, sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('disease_code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('pathogen', sa.String(255)),
        sa.Column('pathogen_type', postgresql.ENUM('bacteria', 'fungus', 'virus', 'insect', 'nematode', 'other', name='pathogentype', create_type=False), nullable=False),
        sa.Column('crop', sa.String(100), nullable=False),
        sa.Column('symptoms', sa.Text),
        sa.Column('severity_scale', postgresql.ARRAY(sa.String)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'disease_code', name='uq_disease_code'),
    )
    op.create_index('ix_disease_org_crop', 'diseases', ['organization_id', 'crop'])
    op.create_index('ix_disease_org_pathogen_type', 'diseases', ['organization_id', 'pathogen_type'])
    
    op.create_table(
        'resistance_genes',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer, sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('disease_id', sa.Integer, sa.ForeignKey('diseases.id'), nullable=False),
        sa.Column('gene_code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('chromosome', sa.String(50)),
        sa.Column('resistance_type', postgresql.ENUM('complete', 'partial', 'recessive', 'dominant', 'quantitative', name='resistancetype', create_type=False), nullable=False),
        sa.Column('source_germplasm', sa.String(255)),
        sa.Column('markers', postgresql.ARRAY(sa.String)),
        sa.Column('reference', sa.Text),
        sa.Column('is_validated', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'gene_code', name='uq_resistance_gene_code'),
    )
    op.create_index('ix_resistance_gene_org_type', 'resistance_genes', ['organization_id', 'resistance_type'])
    
    op.create_table(
        'pyramiding_strategies',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer, sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('strategy_code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('target_disease', sa.String(255)),
        sa.Column('target_stress', sa.String(255)),
        sa.Column('gene_names', postgresql.ARRAY(sa.String), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('status', sa.String(50), default='recommended'),
        sa.Column('warning_message', sa.Text),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'strategy_code', name='uq_pyramiding_strategy_code'),
    )
    
    # ============================================
    # NURSERY MANAGEMENT TABLES
    # ============================================
    
    op.create_table(
        'nursery_locations',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer, sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('location_type', sa.String(100)),
        sa.Column('capacity', sa.Integer),
        sa.Column('description', sa.Text),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'name', name='uq_nursery_location_name'),
    )
    
    op.create_table(
        'seedling_batches',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer, sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('location_id', sa.Integer, sa.ForeignKey('nursery_locations.id')),
        sa.Column('germplasm_id', sa.Integer, sa.ForeignKey('germplasm.id')),
        sa.Column('batch_code', sa.String(50), nullable=False),
        sa.Column('germplasm_name', sa.String(255), nullable=False),
        sa.Column('sowing_date', sa.Date, nullable=False),
        sa.Column('expected_transplant_date', sa.Date),
        sa.Column('actual_transplant_date', sa.Date),
        sa.Column('quantity_sown', sa.Integer, nullable=False),
        sa.Column('quantity_germinated', sa.Integer, default=0),
        sa.Column('quantity_healthy', sa.Integer, default=0),
        sa.Column('quantity_transplanted', sa.Integer, default=0),
        sa.Column('status', postgresql.ENUM('sowing', 'germinating', 'growing', 'ready', 'transplanted', 'failed', name='batchstatus', create_type=False), default='sowing'),
        sa.Column('notes', sa.Text),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'batch_code', name='uq_seedling_batch_code'),
    )
    op.create_index('ix_seedling_batch_org_status', 'seedling_batches', ['organization_id', 'status'])
    op.create_index('ix_seedling_batch_org_location', 'seedling_batches', ['organization_id', 'location_id'])
    
    # ============================================
    # FIELD BOOK TABLES
    # ============================================
    
    op.create_table(
        'field_book_studies',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer, sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('study_id', sa.Integer, sa.ForeignKey('studies.id')),
        sa.Column('study_code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('location', sa.String(255)),
        sa.Column('season', sa.String(100)),
        sa.Column('design', sa.String(100)),
        sa.Column('replications', sa.Integer, default=1),
        sa.Column('total_entries', sa.Integer, default=0),
        sa.Column('total_traits', sa.Integer, default=0),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('data_collection_started', sa.DateTime),
        sa.Column('data_collection_completed', sa.DateTime),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'study_code', name='uq_field_book_study_code'),
    )
    op.create_index('ix_field_book_study_org_active', 'field_book_studies', ['organization_id', 'is_active'])
    
    op.create_table(
        'field_book_traits',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer, sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('study_id', sa.Integer, sa.ForeignKey('field_book_studies.id'), nullable=False),
        sa.Column('variable_id', sa.Integer, sa.ForeignKey('observation_variables.id')),
        sa.Column('trait_code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('unit', sa.String(50)),
        sa.Column('data_type', sa.String(50), default='numeric'),
        sa.Column('min_value', sa.Float),
        sa.Column('max_value', sa.Float),
        sa.Column('step', sa.Float, default=1),
        sa.Column('categories', postgresql.ARRAY(sa.String)),
        sa.Column('display_order', sa.Integer, default=0),
        sa.Column('is_required', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('study_id', 'trait_code', name='uq_field_book_trait_code'),
    )
    op.create_index('ix_field_book_trait_study', 'field_book_traits', ['study_id', 'display_order'])
    
    op.create_table(
        'field_book_entries',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer, sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('study_id', sa.Integer, sa.ForeignKey('field_book_studies.id'), nullable=False),
        sa.Column('germplasm_id', sa.Integer, sa.ForeignKey('germplasm.id')),
        sa.Column('plot_id', sa.String(50), nullable=False),
        sa.Column('germplasm_name', sa.String(255)),
        sa.Column('replication', sa.String(20)),
        sa.Column('block', sa.String(20)),
        sa.Column('row', sa.Integer),
        sa.Column('column', sa.Integer),
        sa.Column('is_check', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('study_id', 'plot_id', name='uq_field_book_entry_plot'),
    )
    op.create_index('ix_field_book_entry_study_rep', 'field_book_entries', ['study_id', 'replication'])
    
    op.create_table(
        'field_book_observations',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer, sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('study_id', sa.Integer, sa.ForeignKey('field_book_studies.id'), nullable=False),
        sa.Column('entry_id', sa.Integer, sa.ForeignKey('field_book_entries.id'), nullable=False),
        sa.Column('trait_id', sa.Integer, sa.ForeignKey('field_book_traits.id'), nullable=False),
        sa.Column('value_numeric', sa.Float),
        sa.Column('value_text', sa.Text),
        sa.Column('value_date', sa.Date),
        sa.Column('observation_timestamp', sa.DateTime, server_default=sa.func.now()),
        sa.Column('collector_id', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('notes', sa.Text),
        sa.Column('latitude', sa.Float),
        sa.Column('longitude', sa.Float),
        sa.Column('is_outlier', sa.Boolean, default=False),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('entry_id', 'trait_id', name='uq_field_book_observation'),
    )
    op.create_index('ix_field_book_obs_study_trait', 'field_book_observations', ['study_id', 'trait_id'])
    op.create_index('ix_field_book_obs_entry', 'field_book_observations', ['entry_id'])


def downgrade() -> None:
    # Drop field book tables
    op.drop_index('ix_field_book_obs_entry', table_name='field_book_observations')
    op.drop_index('ix_field_book_obs_study_trait', table_name='field_book_observations')
    op.drop_table('field_book_observations')
    
    op.drop_index('ix_field_book_entry_study_rep', table_name='field_book_entries')
    op.drop_table('field_book_entries')
    
    op.drop_index('ix_field_book_trait_study', table_name='field_book_traits')
    op.drop_table('field_book_traits')
    
    op.drop_index('ix_field_book_study_org_active', table_name='field_book_studies')
    op.drop_table('field_book_studies')
    
    # Drop nursery tables
    op.drop_index('ix_seedling_batch_org_location', table_name='seedling_batches')
    op.drop_index('ix_seedling_batch_org_status', table_name='seedling_batches')
    op.drop_table('seedling_batches')
    op.drop_table('nursery_locations')
    
    # Drop disease tables
    op.drop_index('ix_resistance_gene_org_type', table_name='resistance_genes')
    op.drop_table('resistance_genes')
    op.drop_table('pyramiding_strategies')
    op.drop_index('ix_disease_org_pathogen_type', table_name='diseases')
    op.drop_index('ix_disease_org_crop', table_name='diseases')
    op.drop_table('diseases')
    
    # Drop abiotic stress tables
    op.drop_index('ix_tolerance_gene_org_crop', table_name='tolerance_genes')
    op.drop_table('tolerance_genes')
    op.drop_index('ix_abiotic_stress_org_category', table_name='abiotic_stresses')
    op.drop_table('abiotic_stresses')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS batchstatus")
    op.execute("DROP TYPE IF EXISTS resistancetype")
    op.execute("DROP TYPE IF EXISTS pathogentype")
    op.execute("DROP TYPE IF EXISTS stresscategory")
