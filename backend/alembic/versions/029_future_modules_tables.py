"""
Create tables for future modules (Tier 1)

Revision ID: 029_future_modules_tables
Revises: 028_fix_datetime_timezone
Create Date: 2026-01-13

Tables Created:
- Crop Intelligence: growing_degree_day_logs, crop_calendars, crop_suitabilities, yield_predictions
- Soil & Nutrients: soil_tests, fertilizer_recommendations, soil_health_scores, carbon_sequestration
- Water & Irrigation: fields, water_balances, irrigation_schedules, soil_moisture_readings
- Crop Protection: disease_risk_forecasts, spray_applications, pest_observations, ipm_strategies

All tables include:
- organization_id FK with index for RLS
- created_at/updated_at timestamps (from BaseModel)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '029'
down_revision = '028'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============= CROP INTELLIGENCE =============
    
    # Growing Degree Day Logs
    op.create_table(
        'growing_degree_day_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=True),
        sa.Column('crop_name', sa.String(100), nullable=False),
        sa.Column('planting_date', sa.Date(), nullable=False),
        sa.Column('log_date', sa.Date(), nullable=False),
        sa.Column('daily_gdd', sa.Float(), nullable=False),
        sa.Column('cumulative_gdd', sa.Float(), nullable=False),
        sa.Column('base_temperature', sa.Float(), nullable=False, server_default='10.0'),
        sa.Column('max_temperature', sa.Float(), nullable=True),
        sa.Column('min_temperature', sa.Float(), nullable=True),
        sa.Column('growth_stage', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.CheckConstraint('daily_gdd >= 0', name='ck_daily_gdd_non_negative'),
        sa.CheckConstraint('cumulative_gdd >= 0', name='ck_cumulative_gdd_non_negative'),
        sa.CheckConstraint('log_date >= planting_date', name='ck_log_date_after_planting'),
    )
    op.create_index('ix_gdd_organization_id', 'growing_degree_day_logs', ['organization_id'])
    op.create_index('ix_gdd_crop_name', 'growing_degree_day_logs', ['crop_name'])
    op.create_index('ix_gdd_log_date', 'growing_degree_day_logs', ['log_date'])

    # Crop Calendars
    op.create_table(
        'crop_calendars',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('crop_name', sa.String(255), nullable=False),
        sa.Column('planting_date', sa.Date(), nullable=True),
        sa.Column('harvest_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_crop_calendars_organization_id', 'crop_calendars', ['organization_id'])
    op.create_index('ix_crop_calendars_crop_name', 'crop_calendars', ['crop_name'])

    # Crop Suitabilities
    op.create_table(
        'crop_suitabilities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('crop_name', sa.String(255), nullable=False),
        sa.Column('variety', sa.String(255), nullable=True),
        sa.Column('suitability_class', sa.String(10), nullable=False),
        sa.Column('suitability_score', sa.Float(), nullable=False),
        sa.Column('climate_score', sa.Float(), nullable=True),
        sa.Column('soil_score', sa.Float(), nullable=True),
        sa.Column('terrain_score', sa.Float(), nullable=True),
        sa.Column('water_score', sa.Float(), nullable=True),
        sa.Column('limiting_factors', postgresql.JSONB(), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(), nullable=True),
        sa.Column('assessment_method', sa.String(100), nullable=True),
        sa.Column('confidence_level', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_crop_suitabilities_organization_id', 'crop_suitabilities', ['organization_id'])
    op.create_index('ix_crop_suitabilities_location_id', 'crop_suitabilities', ['location_id'])
    op.create_index('ix_crop_suitabilities_crop_name', 'crop_suitabilities', ['crop_name'])

    # Yield Predictions
    op.create_table(
        'yield_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=False),
        sa.Column('trial_id', sa.Integer(), nullable=True),
        sa.Column('crop_name', sa.String(255), nullable=False),
        sa.Column('variety', sa.String(255), nullable=True),
        sa.Column('season', sa.String(50), nullable=False),
        sa.Column('predicted_yield', sa.Float(), nullable=False),
        sa.Column('yield_unit', sa.String(50), server_default='t/ha'),
        sa.Column('prediction_date', sa.Date(), nullable=False),
        sa.Column('lower_bound', sa.Float(), nullable=True),
        sa.Column('upper_bound', sa.Float(), nullable=True),
        sa.Column('confidence_level', sa.Float(), server_default='0.95'),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('prediction_method', sa.String(50), nullable=True),
        sa.Column('weather_factors', postgresql.JSONB(), nullable=True),
        sa.Column('soil_factors', postgresql.JSONB(), nullable=True),
        sa.Column('management_factors', postgresql.JSONB(), nullable=True),
        sa.Column('actual_yield', sa.Float(), nullable=True),
        sa.Column('prediction_error', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['field_id'], ['locations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['trial_id'], ['trials.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_yield_predictions_organization_id', 'yield_predictions', ['organization_id'])
    op.create_index('ix_yield_predictions_field_id', 'yield_predictions', ['field_id'])
    op.create_index('ix_yield_predictions_crop_name', 'yield_predictions', ['crop_name'])


    # ============= SOIL & NUTRIENTS =============
    
    # Soil Tests
    op.create_table(
        'soil_tests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=True),
        sa.Column('sample_id', sa.String(255), nullable=False, unique=True),
        sa.Column('sample_date', sa.Date(), nullable=False),
        sa.Column('lab_name', sa.String(255), nullable=True),
        sa.Column('ph', sa.Float(), nullable=True),
        sa.Column('organic_matter_percent', sa.Float(), nullable=True),
        sa.Column('n_ppm', sa.Float(), nullable=True),
        sa.Column('p_ppm', sa.Float(), nullable=True),
        sa.Column('k_ppm', sa.Float(), nullable=True),
        sa.Column('ca_ppm', sa.Float(), nullable=True),
        sa.Column('mg_ppm', sa.Float(), nullable=True),
        sa.Column('s_ppm', sa.Float(), nullable=True),
        sa.Column('zn_ppm', sa.Float(), nullable=True),
        sa.Column('fe_ppm', sa.Float(), nullable=True),
        sa.Column('mn_ppm', sa.Float(), nullable=True),
        sa.Column('cu_ppm', sa.Float(), nullable=True),
        sa.Column('b_ppm', sa.Float(), nullable=True),
        sa.Column('cec', sa.Float(), nullable=True),
        sa.Column('texture_class', sa.String(100), nullable=True),
        sa.Column('sand_percent', sa.Float(), nullable=True),
        sa.Column('silt_percent', sa.Float(), nullable=True),
        sa.Column('clay_percent', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_soil_tests_organization_id', 'soil_tests', ['organization_id'])
    op.create_index('ix_soil_tests_field_id', 'soil_tests', ['field_id'])
    op.create_index('ix_soil_tests_sample_id', 'soil_tests', ['sample_id'])

    # Fertilizer Recommendations
    op.create_table(
        'fertilizer_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('soil_test_id', sa.Integer(), nullable=True),
        sa.Column('field_id', sa.Integer(), nullable=True),
        sa.Column('crop_name', sa.String(100), nullable=False),
        sa.Column('target_yield', sa.Float(), nullable=False),
        sa.Column('yield_unit', sa.String(20), nullable=False, server_default='t/ha'),
        sa.Column('n_kg_ha', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('p_kg_ha', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('k_kg_ha', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('s_kg_ha', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('zn_kg_ha', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('application_timing', postgresql.JSONB(), nullable=True),
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(3), nullable=True, server_default='USD'),
        sa.Column('recommendation_date', sa.Date(), nullable=False),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.CheckConstraint('target_yield > 0', name='ck_target_yield_positive'),
        sa.CheckConstraint('n_kg_ha >= 0', name='ck_n_non_negative'),
        sa.CheckConstraint('p_kg_ha >= 0', name='ck_p_non_negative'),
        sa.CheckConstraint('k_kg_ha >= 0', name='ck_k_non_negative'),
    )
    op.create_index('ix_fertilizer_recommendations_organization_id', 'fertilizer_recommendations', ['organization_id'])
    op.create_index('ix_fertilizer_recommendations_crop_name', 'fertilizer_recommendations', ['crop_name'])

    # Soil Health Scores
    op.create_table(
        'soil_health_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=True),
        sa.Column('assessment_date', sa.Date(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('physical_score', sa.Float(), nullable=True),
        sa.Column('chemical_score', sa.Float(), nullable=True),
        sa.Column('biological_score', sa.Float(), nullable=True),
        sa.Column('organic_carbon_percent', sa.Float(), nullable=True),
        sa.Column('aggregate_stability', sa.Float(), nullable=True),
        sa.Column('water_infiltration_rate', sa.Float(), nullable=True),
        sa.Column('earthworm_count', sa.Integer(), nullable=True),
        sa.Column('microbial_biomass', sa.Float(), nullable=True),
        sa.Column('respiration_rate', sa.Float(), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_soil_health_scores_organization_id', 'soil_health_scores', ['organization_id'])
    op.create_index('ix_soil_health_scores_assessment_date', 'soil_health_scores', ['assessment_date'])

    # Carbon Sequestration
    op.create_table(
        'carbon_sequestration',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=True),
        sa.Column('measurement_date', sa.Date(), nullable=False),
        sa.Column('soil_organic_carbon_baseline', sa.Float(), nullable=False),
        sa.Column('soil_organic_carbon_current', sa.Float(), nullable=False),
        sa.Column('sequestration_rate', sa.Float(), nullable=True),
        sa.Column('measurement_depth_cm', sa.Integer(), nullable=False),
        sa.Column('methodology', sa.String(255), nullable=True),
        sa.Column('verification_status', sa.String(50), server_default='Pending'),
        sa.Column('carbon_credits_potential', sa.Float(), nullable=True),
        sa.Column('practice_changes', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['field_id'], ['locations.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_carbon_sequestration_organization_id', 'carbon_sequestration', ['organization_id'])


    # ============= WATER & IRRIGATION =============
    
    # Fields (for water management)
    op.create_table(
        'fields',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('area_hectares', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_fields_organization_id', 'fields', ['organization_id'])
    op.create_index('ix_fields_name', 'fields', ['name'])

    # Water Balances
    op.create_table(
        'water_balances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=False),
        sa.Column('balance_date', sa.Date(), nullable=False),
        sa.Column('precipitation_mm', sa.Float(), nullable=False),
        sa.Column('irrigation_mm', sa.Float(), nullable=False),
        sa.Column('et_actual_mm', sa.Float(), nullable=False),
        sa.Column('runoff_mm', sa.Float(), nullable=False),
        sa.Column('deep_percolation_mm', sa.Float(), nullable=False),
        sa.Column('soil_water_content_mm', sa.Float(), nullable=False),
        sa.Column('available_water_mm', sa.Float(), nullable=False),
        sa.Column('deficit_mm', sa.Float(), nullable=False),
        sa.Column('surplus_mm', sa.Float(), nullable=False),
        sa.Column('crop_name', sa.String(255), nullable=True),
        sa.Column('growth_stage', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['field_id'], ['fields.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_water_balances_organization_id', 'water_balances', ['organization_id'])
    op.create_index('ix_water_balances_field_id', 'water_balances', ['field_id'])
    op.create_index('ix_water_balances_balance_date', 'water_balances', ['balance_date'])

    # Irrigation Schedules
    op.create_table(
        'irrigation_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=True),
        sa.Column('crop_name', sa.String(255), nullable=False),
        sa.Column('schedule_date', sa.Date(), nullable=False),
        sa.Column('irrigation_method', sa.String(100), nullable=True),
        sa.Column('water_requirement_mm', sa.Float(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.Time(), nullable=True),
        sa.Column('actual_applied_mm', sa.Float(), nullable=True),
        sa.Column('soil_moisture_before', sa.Float(), nullable=True),
        sa.Column('soil_moisture_after', sa.Float(), nullable=True),
        sa.Column('et_reference', sa.Float(), nullable=True),
        sa.Column('crop_coefficient', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), server_default='planned'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_irrigation_schedules_organization_id', 'irrigation_schedules', ['organization_id'])
    op.create_index('ix_irrigation_schedules_schedule_date', 'irrigation_schedules', ['schedule_date'])

    # Soil Moisture Readings
    op.create_table(
        'soil_moisture_readings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=True),
        sa.Column('reading_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('depth_cm', sa.Float(), nullable=False),
        sa.Column('volumetric_water_content', sa.Float(), nullable=False),
        sa.Column('soil_temperature_c', sa.Float(), nullable=True),
        sa.Column('electrical_conductivity', sa.Float(), nullable=True),
        sa.Column('sensor_type', sa.String(50), server_default='soil_moisture'),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lon', sa.Float(), nullable=True),
        sa.Column('battery_level', sa.Integer(), nullable=True),
        sa.Column('signal_strength', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['device_id'], ['iot_devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['field_id'], ['locations.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_soil_moisture_readings_organization_id', 'soil_moisture_readings', ['organization_id'])
    op.create_index('ix_soil_moisture_readings_device_id', 'soil_moisture_readings', ['device_id'])
    op.create_index('ix_soil_moisture_readings_reading_timestamp', 'soil_moisture_readings', ['reading_timestamp'])


    # ============= CROP PROTECTION =============
    
    # Disease Risk Forecasts
    op.create_table(
        'disease_risk_forecasts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('forecast_date', sa.Date(), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('disease_name', sa.String(255), nullable=False),
        sa.Column('crop_name', sa.String(255), nullable=False),
        sa.Column('risk_level', sa.String(50), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('contributing_factors', postgresql.JSONB(), nullable=True),
        sa.Column('recommended_actions', postgresql.JSONB(), nullable=True),
        sa.Column('model_name', sa.String(255), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_disease_risk_forecasts_organization_id', 'disease_risk_forecasts', ['organization_id'])
    op.create_index('ix_disease_risk_forecasts_forecast_date', 'disease_risk_forecasts', ['forecast_date'])
    op.create_index('ix_disease_risk_forecasts_disease_name', 'disease_risk_forecasts', ['disease_name'])
    op.create_index('ix_disease_risk_forecasts_risk_level', 'disease_risk_forecasts', ['risk_level'])

    # Spray Applications
    op.create_table(
        'spray_applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=True),
        sa.Column('application_date', sa.Date(), nullable=False),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('product_type', sa.String(100), nullable=True),
        sa.Column('active_ingredient', sa.String(255), nullable=True),
        sa.Column('rate_per_ha', sa.Float(), nullable=True),
        sa.Column('rate_unit', sa.String(50), nullable=True),
        sa.Column('total_area_ha', sa.Float(), nullable=True),
        sa.Column('water_volume_l_ha', sa.Float(), nullable=True),
        sa.Column('applicator_name', sa.String(255), nullable=True),
        sa.Column('equipment_used', sa.String(255), nullable=True),
        sa.Column('weather_conditions', postgresql.JSONB(), nullable=True),
        sa.Column('target_pest', sa.String(255), nullable=True),
        sa.Column('pre_harvest_interval_days', sa.Integer(), nullable=True),
        sa.Column('re_entry_interval_hours', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_spray_applications_organization_id', 'spray_applications', ['organization_id'])
    op.create_index('ix_spray_applications_application_date', 'spray_applications', ['application_date'])
    op.create_index('ix_spray_applications_product_name', 'spray_applications', ['product_name'])

    # Pest Observations
    op.create_table(
        'pest_observations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=False),
        sa.Column('study_id', sa.Integer(), nullable=True),
        sa.Column('observation_date', sa.Date(), nullable=False),
        sa.Column('observation_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('observer_name', sa.String(255), nullable=True),
        sa.Column('pest_name', sa.String(255), nullable=False),
        sa.Column('pest_type', sa.String(50), nullable=False),
        sa.Column('pest_stage', sa.String(100), nullable=True),
        sa.Column('crop_name', sa.String(255), nullable=False),
        sa.Column('growth_stage', sa.String(100), nullable=True),
        sa.Column('plant_part_affected', sa.String(100), nullable=True),
        sa.Column('severity_score', sa.Float(), nullable=True),
        sa.Column('incidence_percent', sa.Float(), nullable=True),
        sa.Column('count_per_plant', sa.Float(), nullable=True),
        sa.Column('count_per_trap', sa.Float(), nullable=True),
        sa.Column('area_affected_percent', sa.Float(), nullable=True),
        sa.Column('sample_location', sa.String(100), nullable=True),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lon', sa.Float(), nullable=True),
        sa.Column('weather_conditions', postgresql.JSONB(), nullable=True),
        sa.Column('image_urls', postgresql.JSONB(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['field_id'], ['locations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_pest_observations_organization_id', 'pest_observations', ['organization_id'])
    op.create_index('ix_pest_observations_field_id', 'pest_observations', ['field_id'])
    op.create_index('ix_pest_observations_observation_date', 'pest_observations', ['observation_date'])
    op.create_index('ix_pest_observations_pest_name', 'pest_observations', ['pest_name'])

    # IPM Strategies
    op.create_table(
        'ipm_strategies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=True),
        sa.Column('strategy_name', sa.String(255), nullable=False),
        sa.Column('crop_name', sa.String(255), nullable=False),
        sa.Column('target_pest', sa.String(255), nullable=False),
        sa.Column('pest_type', sa.String(50), nullable=True),
        sa.Column('economic_threshold', sa.String(255), nullable=True),
        sa.Column('action_threshold', sa.String(255), nullable=True),
        sa.Column('prevention_methods', postgresql.JSONB(), nullable=True),
        sa.Column('monitoring_methods', postgresql.JSONB(), nullable=True),
        sa.Column('biological_controls', postgresql.JSONB(), nullable=True),
        sa.Column('physical_controls', postgresql.JSONB(), nullable=True),
        sa.Column('chemical_controls', postgresql.JSONB(), nullable=True),
        sa.Column('implementation_start', sa.Date(), nullable=True),
        sa.Column('implementation_end', sa.Date(), nullable=True),
        sa.Column('growth_stages', postgresql.JSONB(), nullable=True),
        sa.Column('effectiveness_rating', sa.Float(), nullable=True),
        sa.Column('cost_effectiveness', sa.Float(), nullable=True),
        sa.Column('environmental_impact_score', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['field_id'], ['locations.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_ipm_strategies_organization_id', 'ipm_strategies', ['organization_id'])
    op.create_index('ix_ipm_strategies_crop_name', 'ipm_strategies', ['crop_name'])
    op.create_index('ix_ipm_strategies_target_pest', 'ipm_strategies', ['target_pest'])


    # ============= ENABLE RLS ON ALL NEW TABLES =============
    
    # Add RLS policies for multi-tenant isolation
    tables_with_rls = [
        'growing_degree_day_logs',
        'crop_calendars',
        'crop_suitabilities',
        'yield_predictions',
        'soil_tests',
        'fertilizer_recommendations',
        'soil_health_scores',
        'carbon_sequestration',
        'fields',
        'water_balances',
        'irrigation_schedules',
        'soil_moisture_readings',
        'disease_risk_forecasts',
        'spray_applications',
        'pest_observations',
        'ipm_strategies',
    ]
    
    for table in tables_with_rls:
        op.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key dependencies)
    
    # Crop Protection
    op.drop_table('ipm_strategies')
    op.drop_table('pest_observations')
    op.drop_table('spray_applications')
    op.drop_table('disease_risk_forecasts')
    
    # Water & Irrigation
    op.drop_table('soil_moisture_readings')
    op.drop_table('irrigation_schedules')
    op.drop_table('water_balances')
    op.drop_table('fields')
    
    # Soil & Nutrients
    op.drop_table('carbon_sequestration')
    op.drop_table('soil_health_scores')
    op.drop_table('fertilizer_recommendations')
    op.drop_table('soil_tests')
    
    # Crop Intelligence
    op.drop_table('yield_predictions')
    op.drop_table('crop_suitabilities')
    op.drop_table('crop_calendars')
    op.drop_table('growing_degree_day_logs')
