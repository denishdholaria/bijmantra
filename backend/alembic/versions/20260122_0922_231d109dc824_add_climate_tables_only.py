"""add_climate_tables_only

Revision ID: 231d109dc824
Revises: deb5cdf8a63f
Create Date: 2026-01-22 09:22:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '231d109dc824'
down_revision = 'a1b2c3d4e5f6'  # Point to the last successful migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create emission_factors table
    op.create_table('emission_factors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.Enum('FERTILIZER', 'FUEL', 'IRRIGATION', 'PESTICIDE', 'MACHINERY', 'TRANSPORT', 'SOIL_N2O', 'OTHER', name='emissioncategory'), nullable=False),
        sa.Column('source_name', sa.String(length=255), nullable=False),
        sa.Column('factor_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=100), nullable=False),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('source_reference', sa.String(length=500), nullable=True),
        sa.Column('valid_from', sa.Date(), nullable=True),
        sa.Column('valid_to', sa.Date(), nullable=True),
        sa.Column('additional_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_emission_factors_category'), 'emission_factors', ['category'], unique=False)
    op.create_index(op.f('ix_emission_factors_organization_id'), 'emission_factors', ['organization_id'], unique=False)
    op.create_index(op.f('ix_emission_factors_source_name'), 'emission_factors', ['source_name'], unique=False)

    # Create carbon_stocks table
    op.create_table('carbon_stocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('measurement_date', sa.Date(), nullable=False),
        sa.Column('soil_carbon_stock', sa.Float(), nullable=True),
        sa.Column('vegetation_carbon_stock', sa.Float(), nullable=True),
        sa.Column('total_carbon_stock', sa.Float(), nullable=False),
        sa.Column('measurement_depth_cm', sa.Integer(), nullable=True),
        sa.Column('measurement_type', sa.Enum('SOIL_ORGANIC', 'VEGETATION_BIOMASS', 'TOTAL_ECOSYSTEM', 'SATELLITE_ESTIMATED', 'FIELD_MEASURED', name='carbonmeasurementtype'), nullable=False),
        sa.Column('confidence_level', sa.Float(), nullable=True),
        sa.Column('gee_image_id', sa.String(length=255), nullable=True),
        sa.Column('additional_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_carbon_stocks_location_id'), 'carbon_stocks', ['location_id'], unique=False)
    op.create_index(op.f('ix_carbon_stocks_measurement_date'), 'carbon_stocks', ['measurement_date'], unique=False)
    op.create_index(op.f('ix_carbon_stocks_organization_id'), 'carbon_stocks', ['organization_id'], unique=False)

    # Create carbon_measurements table
    op.create_table('carbon_measurements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('carbon_stock_id', sa.Integer(), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('measurement_date', sa.Date(), nullable=False),
        sa.Column('measurement_type', sa.Enum('SOIL_ORGANIC', 'VEGETATION_BIOMASS', 'TOTAL_ECOSYSTEM', 'SATELLITE_ESTIMATED', 'FIELD_MEASURED', name='carbonmeasurementtype'), nullable=False),
        sa.Column('carbon_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('depth_from_cm', sa.Integer(), nullable=True),
        sa.Column('depth_to_cm', sa.Integer(), nullable=True),
        sa.Column('bulk_density', sa.Float(), nullable=True),
        sa.Column('sample_id', sa.String(length=100), nullable=True),
        sa.Column('method', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(['carbon_stock_id'], ['carbon_stocks.id'], ),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_carbon_measurements_carbon_stock_id'), 'carbon_measurements', ['carbon_stock_id'], unique=False)
    op.create_index(op.f('ix_carbon_measurements_location_id'), 'carbon_measurements', ['location_id'], unique=False)
    op.create_index(op.f('ix_carbon_measurements_measurement_date'), 'carbon_measurements', ['measurement_date'], unique=False)
    op.create_index(op.f('ix_carbon_measurements_organization_id'), 'carbon_measurements', ['organization_id'], unique=False)

    # Create emission_sources table
    op.create_table('emission_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('trial_id', sa.Integer(), nullable=True),
        sa.Column('study_id', sa.Integer(), nullable=True),
        sa.Column('activity_date', sa.Date(), nullable=False),
        sa.Column('category', sa.Enum('FERTILIZER', 'FUEL', 'IRRIGATION', 'PESTICIDE', 'MACHINERY', 'TRANSPORT', 'SOIL_N2O', 'OTHER', name='emissioncategory'), nullable=False),
        sa.Column('source_name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('emission_factor_id', sa.Integer(), nullable=True),
        sa.Column('co2e_emissions', sa.Float(), nullable=False),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(['emission_factor_id'], ['emission_factors.id'], ),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ),
        sa.ForeignKeyConstraint(['trial_id'], ['trials.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_emission_sources_activity_date'), 'emission_sources', ['activity_date'], unique=False)
    op.create_index(op.f('ix_emission_sources_category'), 'emission_sources', ['category'], unique=False)
    op.create_index(op.f('ix_emission_sources_location_id'), 'emission_sources', ['location_id'], unique=False)
    op.create_index(op.f('ix_emission_sources_organization_id'), 'emission_sources', ['organization_id'], unique=False)
    op.create_index(op.f('ix_emission_sources_study_id'), 'emission_sources', ['study_id'], unique=False)
    op.create_index(op.f('ix_emission_sources_trial_id'), 'emission_sources', ['trial_id'], unique=False)

    # Create variety_footprints table
    op.create_table('variety_footprints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('germplasm_id', sa.Integer(), nullable=False),
        sa.Column('trial_id', sa.Integer(), nullable=True),
        sa.Column('study_id', sa.Integer(), nullable=True),
        sa.Column('season_id', sa.Integer(), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('total_emissions', sa.Float(), nullable=False),
        sa.Column('total_yield', sa.Float(), nullable=False),
        sa.Column('carbon_intensity', sa.Float(), nullable=False),
        sa.Column('emissions_by_category', sa.JSON(), nullable=True),
        sa.Column('measurement_date', sa.Date(), nullable=False),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(['germplasm_id'], ['germplasm.id'], ),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['season_id'], ['seasons.id'], ),
        sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ),
        sa.ForeignKeyConstraint(['trial_id'], ['trials.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_variety_footprints_germplasm_id'), 'variety_footprints', ['germplasm_id'], unique=False)
    op.create_index(op.f('ix_variety_footprints_location_id'), 'variety_footprints', ['location_id'], unique=False)
    op.create_index(op.f('ix_variety_footprints_measurement_date'), 'variety_footprints', ['measurement_date'], unique=False)
    op.create_index(op.f('ix_variety_footprints_organization_id'), 'variety_footprints', ['organization_id'], unique=False)

    # Create impact_metrics table
    op.create_table('impact_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=True),
        sa.Column('metric_type', sa.Enum('HECTARES', 'FARMERS', 'YIELD_IMPROVEMENT', 'CLIMATE_RESILIENCE', 'CARBON_SEQUESTERED', 'EMISSIONS_REDUCED', 'BIODIVERSITY', 'WATER_SAVED', 'ECONOMIC', 'OTHER', name='metrictype'), nullable=False),
        sa.Column('metric_name', sa.String(length=255), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=100), nullable=False),
        sa.Column('baseline_value', sa.Float(), nullable=True),
        sa.Column('measurement_date', sa.Date(), nullable=False),
        sa.Column('geographic_scope', sa.String(length=255), nullable=True),
        sa.Column('beneficiaries', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_impact_metrics_measurement_date'), 'impact_metrics', ['measurement_date'], unique=False)
    op.create_index(op.f('ix_impact_metrics_metric_type'), 'impact_metrics', ['metric_type'], unique=False)
    op.create_index(op.f('ix_impact_metrics_organization_id'), 'impact_metrics', ['organization_id'], unique=False)
    op.create_index(op.f('ix_impact_metrics_program_id'), 'impact_metrics', ['program_id'], unique=False)

    # Create sdg_indicators table
    op.create_table('sdg_indicators',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=True),
        sa.Column('sdg_goal', sa.Enum('SDG_1', 'SDG_2', 'SDG_3', 'SDG_6', 'SDG_7', 'SDG_8', 'SDG_9', 'SDG_12', 'SDG_13', 'SDG_15', 'SDG_17', name='sdggoal'), nullable=False),
        sa.Column('indicator_code', sa.String(length=50), nullable=True),
        sa.Column('indicator_name', sa.String(length=500), nullable=False),
        sa.Column('contribution_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=100), nullable=False),
        sa.Column('measurement_date', sa.Date(), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sdg_indicators_measurement_date'), 'sdg_indicators', ['measurement_date'], unique=False)
    op.create_index(op.f('ix_sdg_indicators_organization_id'), 'sdg_indicators', ['organization_id'], unique=False)
    op.create_index(op.f('ix_sdg_indicators_program_id'), 'sdg_indicators', ['program_id'], unique=False)
    op.create_index(op.f('ix_sdg_indicators_sdg_goal'), 'sdg_indicators', ['sdg_goal'], unique=False)

    # Create variety_releases table
    op.create_table('variety_releases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('germplasm_id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=True),
        sa.Column('release_name', sa.String(length=255), nullable=False),
        sa.Column('release_date', sa.Date(), nullable=False),
        sa.Column('release_status', sa.Enum('PENDING', 'APPROVED', 'RELEASED', 'WITHDRAWN', name='releasestatus'), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('region', sa.String(length=255), nullable=True),
        sa.Column('releasing_authority', sa.String(length=255), nullable=False),
        sa.Column('registration_number', sa.String(length=100), nullable=True),
        sa.Column('target_environment', sa.String(length=500), nullable=True),
        sa.Column('expected_adoption_ha', sa.Float(), nullable=True),
        sa.Column('actual_adoption_ha', sa.Float(), nullable=True),
        sa.Column('documentation_url', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['germplasm_id'], ['germplasm.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_variety_releases_germplasm_id'), 'variety_releases', ['germplasm_id'], unique=False)
    op.create_index(op.f('ix_variety_releases_organization_id'), 'variety_releases', ['organization_id'], unique=False)
    op.create_index(op.f('ix_variety_releases_program_id'), 'variety_releases', ['program_id'], unique=False)
    op.create_index(op.f('ix_variety_releases_release_date'), 'variety_releases', ['release_date'], unique=False)

    # Create policy_adoptions table
    op.create_table('policy_adoptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=True),
        sa.Column('germplasm_id', sa.Integer(), nullable=True),
        sa.Column('policy_name', sa.String(length=500), nullable=False),
        sa.Column('adoption_date', sa.Date(), nullable=False),
        sa.Column('adoption_level', sa.Enum('PILOT', 'REGIONAL', 'NATIONAL', 'INTERNATIONAL', name='adoptionlevel'), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('region', sa.String(length=255), nullable=True),
        sa.Column('government_body', sa.String(length=255), nullable=False),
        sa.Column('budget_allocated', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('target_farmers', sa.Integer(), nullable=True),
        sa.Column('target_hectares', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('documentation_url', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['germplasm_id'], ['germplasm.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_policy_adoptions_adoption_date'), 'policy_adoptions', ['adoption_date'], unique=False)
    op.create_index(op.f('ix_policy_adoptions_germplasm_id'), 'policy_adoptions', ['germplasm_id'], unique=False)
    op.create_index(op.f('ix_policy_adoptions_organization_id'), 'policy_adoptions', ['organization_id'], unique=False)
    op.create_index(op.f('ix_policy_adoptions_program_id'), 'policy_adoptions', ['program_id'], unique=False)

    # Create publications table
    op.create_table('publications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=1000), nullable=False),
        sa.Column('authors', sa.Text(), nullable=False),
        sa.Column('journal', sa.String(length=500), nullable=True),
        sa.Column('publication_date', sa.Date(), nullable=False),
        sa.Column('doi', sa.String(length=255), nullable=True),
        sa.Column('url', sa.String(length=500), nullable=True),
        sa.Column('citation_count', sa.Integer(), nullable=True),
        sa.Column('impact_factor', sa.Float(), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('bijmantra_usage', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_publications_organization_id'), 'publications', ['organization_id'], unique=False)
    op.create_index(op.f('ix_publications_program_id'), 'publications', ['program_id'], unique=False)
    op.create_index(op.f('ix_publications_publication_date'), 'publications', ['publication_date'], unique=False)

    # Create impact_reports table
    op.create_table('impact_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=True),
        sa.Column('report_title', sa.String(length=500), nullable=False),
        sa.Column('report_type', sa.String(length=100), nullable=False),
        sa.Column('reporting_period_start', sa.Date(), nullable=False),
        sa.Column('reporting_period_end', sa.Date(), nullable=False),
        sa.Column('generated_date', sa.Date(), nullable=False),
        sa.Column('generated_by_user_id', sa.Integer(), nullable=False),
        sa.Column('report_data', sa.JSON(), nullable=False),
        sa.Column('file_url', sa.String(length=500), nullable=True),
        sa.Column('format', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['generated_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_impact_reports_generated_date'), 'impact_reports', ['generated_date'], unique=False)
    op.create_index(op.f('ix_impact_reports_organization_id'), 'impact_reports', ['organization_id'], unique=False)
    op.create_index(op.f('ix_impact_reports_program_id'), 'impact_reports', ['program_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('impact_reports')
    op.drop_table('publications')
    op.drop_table('policy_adoptions')
    op.drop_table('variety_releases')
    op.drop_table('sdg_indicators')
    op.drop_table('impact_metrics')
    op.drop_table('variety_footprints')
    op.drop_table('emission_sources')
    op.drop_table('carbon_measurements')
    op.drop_table('carbon_stocks')
    op.drop_table('emission_factors')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS emissioncategory')
    op.execute('DROP TYPE IF EXISTS carbonmeasurementtype')
    op.execute('DROP TYPE IF EXISTS metrictype')
    op.execute('DROP TYPE IF EXISTS sdggoal')
    op.execute('DROP TYPE IF EXISTS releasestatus')
    op.execute('DROP TYPE IF EXISTS adoptionlevel')
