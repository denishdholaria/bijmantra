"""Add genotyping tables for BrAPI Genotyping module

Revision ID: 011_genotyping_tables
Revises: 010
Create Date: 2025-12-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011_genotyping_tables'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Reference Sets table
    op.create_table(
        'reference_sets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('reference_set_db_id', sa.String(255), nullable=True),
        sa.Column('reference_set_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('assembly_pui', sa.String(255), nullable=True),
        sa.Column('source_uri', sa.Text(), nullable=True),
        sa.Column('source_accessions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('source_germplasm', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('species', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_derived', sa.Boolean(), default=False),
        sa.Column('md5checksum', sa.String(32), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reference_sets_organization_id', 'reference_sets', ['organization_id'])
    op.create_index('ix_reference_sets_reference_set_db_id', 'reference_sets', ['reference_set_db_id'], unique=True)
    op.create_index('ix_reference_sets_reference_set_name', 'reference_sets', ['reference_set_name'])

    # References table
    op.create_table(
        'references',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('reference_set_id', sa.Integer(), nullable=True),
        sa.Column('reference_db_id', sa.String(255), nullable=True),
        sa.Column('reference_name', sa.String(255), nullable=False),
        sa.Column('length', sa.Integer(), nullable=True),
        sa.Column('md5checksum', sa.String(32), nullable=True),
        sa.Column('source_uri', sa.Text(), nullable=True),
        sa.Column('source_accessions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('source_divergence', sa.Float(), nullable=True),
        sa.Column('species', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_derived', sa.Boolean(), default=False),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['reference_set_id'], ['reference_sets.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_references_organization_id', 'references', ['organization_id'])
    op.create_index('ix_references_reference_set_id', 'references', ['reference_set_id'])
    op.create_index('ix_references_reference_db_id', 'references', ['reference_db_id'], unique=True)
    op.create_index('ix_references_reference_name', 'references', ['reference_name'])

    # Genome Maps table
    op.create_table(
        'genome_maps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('map_db_id', sa.String(255), nullable=True),
        sa.Column('map_name', sa.String(255), nullable=False),
        sa.Column('map_pui', sa.String(255), nullable=True),
        sa.Column('common_crop_name', sa.String(100), nullable=True),
        sa.Column('type', sa.String(50), nullable=True),
        sa.Column('unit', sa.String(20), nullable=True),
        sa.Column('scientific_name', sa.String(255), nullable=True),
        sa.Column('published_date', sa.String(50), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('documentation_url', sa.Text(), nullable=True),
        sa.Column('linkage_group_count', sa.Integer(), nullable=True),
        sa.Column('marker_count', sa.Integer(), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_genome_maps_organization_id', 'genome_maps', ['organization_id'])
    op.create_index('ix_genome_maps_map_db_id', 'genome_maps', ['map_db_id'], unique=True)
    op.create_index('ix_genome_maps_map_name', 'genome_maps', ['map_name'])

    # Linkage Groups table
    op.create_table(
        'linkage_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('map_id', sa.Integer(), nullable=False),
        sa.Column('linkage_group_name', sa.String(100), nullable=False),
        sa.Column('max_position', sa.Float(), nullable=True),
        sa.Column('marker_count', sa.Integer(), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['map_id'], ['genome_maps.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_linkage_groups_organization_id', 'linkage_groups', ['organization_id'])
    op.create_index('ix_linkage_groups_map_id', 'linkage_groups', ['map_id'])
    op.create_index('ix_linkage_groups_linkage_group_name', 'linkage_groups', ['linkage_group_name'])

    # Marker Positions table
    op.create_table(
        'marker_positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('map_id', sa.Integer(), nullable=False),
        sa.Column('marker_position_db_id', sa.String(255), nullable=True),
        sa.Column('variant_db_id', sa.String(255), nullable=True),
        sa.Column('variant_name', sa.String(255), nullable=True),
        sa.Column('linkage_group_name', sa.String(100), nullable=True),
        sa.Column('position', sa.Float(), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['map_id'], ['genome_maps.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_marker_positions_organization_id', 'marker_positions', ['organization_id'])
    op.create_index('ix_marker_positions_map_id', 'marker_positions', ['map_id'])
    op.create_index('ix_marker_positions_marker_position_db_id', 'marker_positions', ['marker_position_db_id'], unique=True)
    op.create_index('ix_marker_positions_variant_db_id', 'marker_positions', ['variant_db_id'])
    op.create_index('ix_marker_positions_linkage_group_name', 'marker_positions', ['linkage_group_name'])

    # Variant Sets table
    op.create_table(
        'variant_sets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('reference_set_id', sa.Integer(), nullable=True),
        sa.Column('study_id', sa.Integer(), nullable=True),
        sa.Column('variant_set_db_id', sa.String(255), nullable=True),
        sa.Column('variant_set_name', sa.String(255), nullable=False),
        sa.Column('analysis', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('available_formats', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('call_set_count', sa.Integer(), nullable=True),
        sa.Column('variant_count', sa.Integer(), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['reference_set_id'], ['reference_sets.id']),
        sa.ForeignKeyConstraint(['study_id'], ['studies.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_variant_sets_organization_id', 'variant_sets', ['organization_id'])
    op.create_index('ix_variant_sets_reference_set_id', 'variant_sets', ['reference_set_id'])
    op.create_index('ix_variant_sets_study_id', 'variant_sets', ['study_id'])
    op.create_index('ix_variant_sets_variant_set_db_id', 'variant_sets', ['variant_set_db_id'], unique=True)
    op.create_index('ix_variant_sets_variant_set_name', 'variant_sets', ['variant_set_name'])

    # Variants table
    op.create_table(
        'variants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('variant_set_id', sa.Integer(), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('variant_db_id', sa.String(255), nullable=True),
        sa.Column('variant_name', sa.String(255), nullable=True),
        sa.Column('variant_type', sa.String(50), nullable=True),
        sa.Column('reference_bases', sa.Text(), nullable=True),
        sa.Column('alternate_bases', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('start', sa.Integer(), nullable=True),
        sa.Column('end', sa.Integer(), nullable=True),
        sa.Column('cipos', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ciend', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('svlen', sa.Integer(), nullable=True),
        sa.Column('filters_applied', sa.Boolean(), default=True),
        sa.Column('filters_passed', sa.Boolean(), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['variant_set_id'], ['variant_sets.id']),
        sa.ForeignKeyConstraint(['reference_id'], ['references.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_variants_organization_id', 'variants', ['organization_id'])
    op.create_index('ix_variants_variant_set_id', 'variants', ['variant_set_id'])
    op.create_index('ix_variants_reference_id', 'variants', ['reference_id'])
    op.create_index('ix_variants_variant_db_id', 'variants', ['variant_db_id'], unique=True)
    op.create_index('ix_variants_variant_name', 'variants', ['variant_name'])
    op.create_index('ix_variants_start', 'variants', ['start'])

    # Call Sets table
    op.create_table(
        'call_sets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('sample_id', sa.Integer(), nullable=True),
        sa.Column('call_set_db_id', sa.String(255), nullable=True),
        sa.Column('call_set_name', sa.String(255), nullable=False),
        sa.Column('sample_db_id', sa.String(255), nullable=True),
        sa.Column('created', sa.String(50), nullable=True),
        sa.Column('updated', sa.String(50), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['sample_id'], ['samples.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_call_sets_organization_id', 'call_sets', ['organization_id'])
    op.create_index('ix_call_sets_sample_id', 'call_sets', ['sample_id'])
    op.create_index('ix_call_sets_call_set_db_id', 'call_sets', ['call_set_db_id'], unique=True)
    op.create_index('ix_call_sets_call_set_name', 'call_sets', ['call_set_name'])
    op.create_index('ix_call_sets_sample_db_id', 'call_sets', ['sample_db_id'])

    # Variant Set - Call Set association table
    op.create_table(
        'variant_set_call_sets',
        sa.Column('variant_set_id', sa.Integer(), nullable=False),
        sa.Column('call_set_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['variant_set_id'], ['variant_sets.id']),
        sa.ForeignKeyConstraint(['call_set_id'], ['call_sets.id']),
        sa.PrimaryKeyConstraint('variant_set_id', 'call_set_id')
    )

    # Calls table
    op.create_table(
        'calls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('variant_id', sa.Integer(), nullable=False),
        sa.Column('call_set_id', sa.Integer(), nullable=False),
        sa.Column('call_db_id', sa.String(255), nullable=True),
        sa.Column('genotype', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('genotype_value', sa.String(50), nullable=True),
        sa.Column('genotype_likelihood', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('phaseSet', sa.String(255), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id']),
        sa.ForeignKeyConstraint(['call_set_id'], ['call_sets.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_calls_organization_id', 'calls', ['organization_id'])
    op.create_index('ix_calls_variant_id', 'calls', ['variant_id'])
    op.create_index('ix_calls_call_set_id', 'calls', ['call_set_id'])
    op.create_index('ix_calls_call_db_id', 'calls', ['call_db_id'], unique=True)

    # Plates table
    op.create_table(
        'plates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('study_id', sa.Integer(), nullable=True),
        sa.Column('trial_id', sa.Integer(), nullable=True),
        sa.Column('program_id', sa.Integer(), nullable=True),
        sa.Column('plate_db_id', sa.String(255), nullable=True),
        sa.Column('plate_name', sa.String(255), nullable=False),
        sa.Column('plate_barcode', sa.String(255), nullable=True),
        sa.Column('plate_format', sa.String(50), nullable=True),
        sa.Column('sample_type', sa.String(100), nullable=True),
        sa.Column('status_time_stamp', sa.String(50), nullable=True),
        sa.Column('client_plate_db_id', sa.String(255), nullable=True),
        sa.Column('client_plate_barcode', sa.String(255), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['study_id'], ['studies.id']),
        sa.ForeignKeyConstraint(['trial_id'], ['trials.id']),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_plates_organization_id', 'plates', ['organization_id'])
    op.create_index('ix_plates_study_id', 'plates', ['study_id'])
    op.create_index('ix_plates_trial_id', 'plates', ['trial_id'])
    op.create_index('ix_plates_program_id', 'plates', ['program_id'])
    op.create_index('ix_plates_plate_db_id', 'plates', ['plate_db_id'], unique=True)
    op.create_index('ix_plates_plate_name', 'plates', ['plate_name'])
    op.create_index('ix_plates_plate_barcode', 'plates', ['plate_barcode'])

    # Vendor Orders table
    op.create_table(
        'vendor_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('order_db_id', sa.String(255), nullable=True),
        sa.Column('client_id', sa.String(255), nullable=True),
        sa.Column('number_of_samples', sa.Integer(), nullable=True),
        sa.Column('order_id', sa.String(255), nullable=True),
        sa.Column('required_service_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('service_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('status_time_stamp', sa.String(50), nullable=True),
        sa.Column('additional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_references', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_vendor_orders_organization_id', 'vendor_orders', ['organization_id'])
    op.create_index('ix_vendor_orders_order_db_id', 'vendor_orders', ['order_db_id'], unique=True)
    op.create_index('ix_vendor_orders_client_id', 'vendor_orders', ['client_id'])


def downgrade() -> None:
    op.drop_table('vendor_orders')
    op.drop_table('plates')
    op.drop_table('calls')
    op.drop_table('variant_set_call_sets')
    op.drop_table('call_sets')
    op.drop_table('variants')
    op.drop_table('variant_sets')
    op.drop_table('marker_positions')
    op.drop_table('linkage_groups')
    op.drop_table('genome_maps')
    op.drop_table('references')
    op.drop_table('reference_sets')
