"""Add performance tables

Revision ID: 20260217_0000
Revises: 20260216_0939
Create Date: 2026-02-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260217_0000'
down_revision = '20260216_0939'
branch_labels = None
depends_on = None


def upgrade():
    # DatabaseIndex
    op.create_table('perf_database_indexes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('table_name', sa.String(), nullable=False),
        sa.Column('index_name', sa.String(), nullable=False),
        sa.Column('columns', sa.JSON(), nullable=False),
        sa.Column('is_unique', sa.Boolean(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_perf_database_indexes_id'), 'perf_database_indexes', ['id'], unique=False)
    op.create_index(op.f('ix_perf_database_indexes_index_name'), 'perf_database_indexes', ['index_name'], unique=True)
    op.create_index(op.f('ix_perf_database_indexes_table_name'), 'perf_database_indexes', ['table_name'], unique=False)

    # QueryCache
    op.create_table('perf_query_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('query_hash', sa.String(), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('hit_count', sa.Integer(), nullable=True),
        sa.Column('miss_count', sa.Integer(), nullable=True),
        sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_perf_query_cache_id'), 'perf_query_cache', ['id'], unique=False)
    op.create_index(op.f('ix_perf_query_cache_query_hash'), 'perf_query_cache', ['query_hash'], unique=True)

    # FrontendBundle
    op.create_table('perf_frontend_bundles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('size_kb', sa.Float(), nullable=False),
        sa.Column('load_time_ms', sa.Integer(), nullable=True),
        sa.Column('build_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_perf_frontend_bundles_build_id'), 'perf_frontend_bundles', ['build_id'], unique=False)
    op.create_index(op.f('ix_perf_frontend_bundles_id'), 'perf_frontend_bundles', ['id'], unique=False)
    op.create_index(op.f('ix_perf_frontend_bundles_name'), 'perf_frontend_bundles', ['name'], unique=False)

    # AssetOptimization
    op.create_table('perf_asset_optimizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('asset_path', sa.String(), nullable=False),
        sa.Column('original_size_kb', sa.Float(), nullable=False),
        sa.Column('optimized_size_kb', sa.Float(), nullable=False),
        sa.Column('compression_ratio', sa.Float(), nullable=True),
        sa.Column('optimization_method', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_perf_asset_optimizations_asset_path'), 'perf_asset_optimizations', ['asset_path'], unique=True)
    op.create_index(op.f('ix_perf_asset_optimizations_id'), 'perf_asset_optimizations', ['id'], unique=False)

    # ServerResponse
    op.create_table('perf_server_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('endpoint', sa.String(), nullable=False),
        sa.Column('method', sa.String(), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Float(), nullable=False),
        sa.Column('client_ip', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_perf_server_responses_endpoint'), 'perf_server_responses', ['endpoint'], unique=False)
    op.create_index(op.f('ix_perf_server_responses_id'), 'perf_server_responses', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_perf_server_responses_id'), table_name='perf_server_responses')
    op.drop_index(op.f('ix_perf_server_responses_endpoint'), table_name='perf_server_responses')
    op.drop_table('perf_server_responses')

    op.drop_index(op.f('ix_perf_asset_optimizations_id'), table_name='perf_asset_optimizations')
    op.drop_index(op.f('ix_perf_asset_optimizations_asset_path'), table_name='perf_asset_optimizations')
    op.drop_table('perf_asset_optimizations')

    op.drop_index(op.f('ix_perf_frontend_bundles_name'), table_name='perf_frontend_bundles')
    op.drop_index(op.f('ix_perf_frontend_bundles_id'), table_name='perf_frontend_bundles')
    op.drop_index(op.f('ix_perf_frontend_bundles_build_id'), table_name='perf_frontend_bundles')
    op.drop_table('perf_frontend_bundles')

    op.drop_index(op.f('ix_perf_query_cache_query_hash'), table_name='perf_query_cache')
    op.drop_index(op.f('ix_perf_query_cache_id'), table_name='perf_query_cache')
    op.drop_table('perf_query_cache')

    op.drop_index(op.f('ix_perf_database_indexes_table_name'), table_name='perf_database_indexes')
    op.drop_index(op.f('ix_perf_database_indexes_index_name'), table_name='perf_database_indexes')
    op.drop_index(op.f('ix_perf_database_indexes_id'), table_name='perf_database_indexes')
    op.drop_table('perf_database_indexes')
