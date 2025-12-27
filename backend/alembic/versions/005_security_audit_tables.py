"""Security audit tables

Revision ID: 005_security_audit
Revises: 004_seed_bank_tables
Create Date: 2025-12-11

Creates tables for:
- security_audit_log: Persistent audit logging
- security_threats: Detected threat records
- security_responses: Response action records
- security_blocked: Blocked entities (backup to Redis)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '005_security_audit'
down_revision = '004_seed_bank'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Security Audit Log
    op.create_table(
        'security_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('category', sa.String(50), nullable=False, index=True),
        sa.Column('severity', sa.String(20), nullable=False, index=True),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('actor', sa.String(255), nullable=True, index=True),
        sa.Column('target', sa.String(500), nullable=True, index=True),
        sa.Column('source_ip', sa.String(45), nullable=True, index=True),
        sa.Column('details', postgresql.JSON(), nullable=True),
        sa.Column('success', sa.Boolean(), default=True, nullable=False),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('request_id', sa.String(100), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
    )
    
    # Composite indexes for audit log
    op.create_index('ix_audit_timestamp_category', 'security_audit_log', ['timestamp', 'category'])
    op.create_index('ix_audit_actor_timestamp', 'security_audit_log', ['actor', 'timestamp'])
    op.create_index('ix_audit_source_ip_timestamp', 'security_audit_log', ['source_ip', 'timestamp'])
    op.create_index('ix_audit_severity_timestamp', 'security_audit_log', ['severity', 'timestamp'])
    
    # Security Threats
    op.create_table(
        'security_threats',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('category', sa.String(50), nullable=False, index=True),
        sa.Column('confidence', sa.String(20), nullable=False),
        sa.Column('confidence_score', sa.Integer(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, index=True),
        sa.Column('source_ip', sa.String(45), nullable=True, index=True),
        sa.Column('user_id', sa.String(255), nullable=True, index=True),
        sa.Column('event_id', sa.String(100), nullable=True),
        sa.Column('indicators', postgresql.JSON(), nullable=True),
        sa.Column('recommended_actions', postgresql.JSON(), nullable=True),
        sa.Column('resolved', sa.Boolean(), default=False, nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(255), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
    )
    
    # Security Responses
    op.create_table(
        'security_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('action', sa.String(50), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('target_type', sa.String(20), nullable=True),
        sa.Column('target', sa.String(255), nullable=True, index=True),
        sa.Column('threat_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('triggered_by', sa.String(50), nullable=True),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('executed_by', sa.String(255), nullable=True),
    )
    
    # Blocked Entities
    op.create_table(
        'security_blocked',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', sa.String(20), nullable=False, index=True),
        sa.Column('entity_value', sa.String(255), nullable=False, index=True),
        sa.Column('blocked_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('blocked_by', sa.String(255), nullable=True),
        sa.Column('threat_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    
    # Unique constraint for blocked entities
    op.create_index('ix_blocked_entity', 'security_blocked', ['entity_type', 'entity_value'], unique=True)


def downgrade() -> None:
    op.drop_table('security_blocked')
    op.drop_table('security_responses')
    op.drop_table('security_threats')
    op.drop_table('security_audit_log')
