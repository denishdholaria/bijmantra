"""Add vector store tables

Revision ID: 003_vector_store
Revises: 002
Create Date: 2024-12-04

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_vector_store'
down_revision = '001'  # Fixed: was '002' which doesn't exist
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create vector_documents table
    op.create_table(
        'vector_documents',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('doc_id', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('doc_type', sa.String(), nullable=False, index=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(), nullable=True, index=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('source_id', sa.String(), nullable=True, index=True),
        sa.Column('source_type', sa.String(), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Add vector column (384 dimensions for MiniLM model)
    op.execute('ALTER TABLE vector_documents ADD COLUMN embedding vector(384)')
    
    # Create IVFFlat index for fast similarity search
    # lists = sqrt(n) where n is expected number of rows
    # Starting with 100 lists, can be adjusted as data grows
    op.execute('''
        CREATE INDEX ix_vector_documents_embedding 
        ON vector_documents 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    ''')
    
    # Create composite index for common queries
    op.create_index(
        'ix_vector_doc_type_source',
        'vector_documents',
        ['doc_type', 'source_type']
    )


def downgrade() -> None:
    op.drop_index('ix_vector_doc_type_source', table_name='vector_documents')
    op.drop_index('ix_vector_documents_embedding', table_name='vector_documents')
    op.drop_table('vector_documents')
    # Note: We don't drop the vector extension as other tables might use it
