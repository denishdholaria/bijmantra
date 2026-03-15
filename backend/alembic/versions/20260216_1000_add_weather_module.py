"""add_weather_module

Revision ID: b40f25e73059
Revises: 9dd8db50eb6e
Create Date: 2026-02-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = 'b40f25e73059'
down_revision = '9dd8db50eb6e'
branch_labels = None
depends_on = None


def upgrade():
    # Weather Stations
    op.create_table('weather_stations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('elevation', sa.Float(), nullable=True),
        sa.Column('provider', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('additional_info', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_weather_stations_id'), 'weather_stations', ['id'], unique=False)
    op.create_index(op.f('ix_weather_stations_name'), 'weather_stations', ['name'], unique=False)

    # Weather Forecasts
    op.create_table('weather_forecasts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('station_id', sa.Integer(), nullable=False),
        sa.Column('forecast_date', sa.Date(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('source', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['station_id'], ['weather_stations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_weather_forecasts_id'), 'weather_forecasts', ['id'], unique=False)
    op.create_index(op.f('ix_weather_forecasts_station_id'), 'weather_forecasts', ['station_id'], unique=False)
    op.create_index(op.f('ix_weather_forecasts_forecast_date'), 'weather_forecasts', ['forecast_date'], unique=False)

    # Weather Historical
    op.create_table('weather_historical',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('station_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('temperature_max', sa.Float(), nullable=True),
        sa.Column('temperature_min', sa.Float(), nullable=True),
        sa.Column('precipitation', sa.Float(), nullable=True),
        sa.Column('humidity', sa.Float(), nullable=True),
        sa.Column('wind_speed', sa.Float(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['station_id'], ['weather_stations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_weather_historical_id'), 'weather_historical', ['id'], unique=False)
    op.create_index(op.f('ix_weather_historical_station_id'), 'weather_historical', ['station_id'], unique=False)
    op.create_index(op.f('ix_weather_historical_date'), 'weather_historical', ['date'], unique=False)

    # Climate Zones
    op.create_table('climate_zones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
        sa.Column('additional_info', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_climate_zones_id'), 'climate_zones', ['id'], unique=False)
    op.create_index(op.f('ix_climate_zones_name'), 'climate_zones', ['name'], unique=False)

    # Weather Alert Subscriptions
    op.create_table('weather_alert_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('station_id', sa.Integer(), nullable=True),
        sa.Column('alert_type', sa.String(), nullable=False),
        sa.Column('threshold', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.ForeignKeyConstraint(['station_id'], ['weather_stations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_weather_alert_subscriptions_id'), 'weather_alert_subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_weather_alert_subscriptions_user_id'), 'weather_alert_subscriptions', ['user_id'], unique=False)


def downgrade():
    op.drop_table('weather_alert_subscriptions')
    op.drop_table('climate_zones')
    op.drop_table('weather_historical')
    op.drop_table('weather_forecasts')
    op.drop_table('weather_stations')
