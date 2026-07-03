"""add_crop_calendar_module

Revision ID: abcdef123456
Revises: 9dd8db50eb6e
Create Date: 2026-02-16 10:00:00.000000+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abcdef123456'
down_revision = '9dd8db50eb6e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old table if exists
    op.execute("DROP TABLE IF EXISTS crop_calendars CASCADE")

    # ActivityType
    op.create_table('activity_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_types_id'), 'activity_types', ['id'], unique=False)
    op.create_index(op.f('ix_activity_types_organization_id'), 'activity_types', ['organization_id'], unique=False)

    # GrowthStage
    op.create_table('growth_stages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('crop_id', sa.String(length=255), nullable=False),
        sa.Column('stage_name', sa.String(length=255), nullable=False),
        sa.Column('days_from_sowing', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_growth_stages_id'), 'growth_stages', ['id'], unique=False)
    op.create_index(op.f('ix_growth_stages_organization_id'), 'growth_stages', ['organization_id'], unique=False)
    op.create_index(op.f('ix_growth_stages_crop_id'), 'growth_stages', ['crop_id'], unique=False)

    # CropCalendar
    op.create_table('crop_calendars',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('crop_id', sa.String(length=255), nullable=False),
        sa.Column('trial_id', sa.String(length=255), nullable=True),
        sa.Column('planting_date', sa.Date(), nullable=False),
        sa.Column('expected_harvest_date', sa.Date(), nullable=True),
        sa.Column('actual_harvest_date', sa.Date(), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('location_name', sa.String(length=255), nullable=True),
        sa.Column('area_hectares', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crop_calendars_id'), 'crop_calendars', ['id'], unique=False)
    op.create_index(op.f('ix_crop_calendars_organization_id'), 'crop_calendars', ['organization_id'], unique=False)
    op.create_index(op.f('ix_crop_calendars_crop_id'), 'crop_calendars', ['crop_id'], unique=False)
    op.create_index(op.f('ix_crop_calendars_trial_id'), 'crop_calendars', ['trial_id'], unique=False)

    # ScheduleEvent
    op.create_table('schedule_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('calendar_id', sa.Integer(), nullable=False),
        sa.Column('activity_type_id', sa.Integer(), nullable=True),
        sa.Column('activity_name', sa.String(length=255), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('completed_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['activity_type_id'], ['activity_types.id'], ),
        sa.ForeignKeyConstraint(['calendar_id'], ['crop_calendars.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_events_id'), 'schedule_events', ['id'], unique=False)
    op.create_index(op.f('ix_schedule_events_organization_id'), 'schedule_events', ['organization_id'], unique=False)
    op.create_index(op.f('ix_schedule_events_calendar_id'), 'schedule_events', ['calendar_id'], unique=False)

    # ResourceRequirement
    op.create_table('resource_requirements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('resource_type', sa.String(length=255), nullable=False),
        sa.Column('resource_name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('cost_estimate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['schedule_events.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resource_requirements_id'), 'resource_requirements', ['id'], unique=False)
    op.create_index(op.f('ix_resource_requirements_organization_id'), 'resource_requirements', ['organization_id'], unique=False)
    op.create_index(op.f('ix_resource_requirements_event_id'), 'resource_requirements', ['event_id'], unique=False)

    # HarvestWindow
    op.create_table('harvest_windows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('calendar_id', sa.Integer(), nullable=False),
        sa.Column('window_start', sa.Date(), nullable=False),
        sa.Column('window_end', sa.Date(), nullable=False),
        sa.Column('predicted_yield', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('confidence_level', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['calendar_id'], ['crop_calendars.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_harvest_windows_id'), 'harvest_windows', ['id'], unique=False)
    op.create_index(op.f('ix_harvest_windows_organization_id'), 'harvest_windows', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_table('harvest_windows')
    op.drop_table('resource_requirements')
    op.drop_table('schedule_events')
    op.drop_table('crop_calendars')
    op.drop_table('growth_stages')
    op.drop_table('activity_types')

    op.create_table('crop_calendars',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('crop_name', sa.String(length=255), nullable=False),
        sa.Column('planting_date', sa.Date(), nullable=True),
        sa.Column('harvest_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
