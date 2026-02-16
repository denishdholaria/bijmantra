"""
BrAPI Genotyping Module Models
Variants, CallSets, Calls, References, ReferenceSets, Maps, MarkerPositions, Plates
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Float, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ReferenceSet(BaseModel):
    """BrAPI Reference Set - A set of reference sequences (genome assembly)"""

    __tablename__ = "reference_sets"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    reference_set_db_id = Column(String(255), unique=True, index=True)
    reference_set_name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    assembly_pui = Column(String(255))
    source_uri = Column(Text)
    source_accessions = Column(JSON)  # List of accession strings
    source_germplasm = Column(JSON)  # List of germplasm objects
    species = Column(JSON)  # Species object with term, termURI
    is_derived = Column(Boolean, default=False)
    md5checksum = Column(String(32))

    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)

    # Relationships
    organization = relationship("Organization")
    references = relationship("Reference", back_populates="reference_set", cascade="all, delete-orphan")


class Reference(BaseModel):
    """BrAPI Reference - A reference sequence (chromosome/contig)"""

    __tablename__ = "references"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    reference_set_id = Column(Integer, ForeignKey("reference_sets.id"), index=True)

    reference_db_id = Column(String(255), unique=True, index=True)
    reference_name = Column(String(255), nullable=False, index=True)
    length = Column(Integer)
    md5checksum = Column(String(32))
    source_uri = Column(Text)
    source_accessions = Column(JSON)
    source_divergence = Column(Float)
    species = Column(JSON)
    is_derived = Column(Boolean, default=False)

    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)

    # Relationships
    organization = relationship("Organization")
    reference_set = relationship("ReferenceSet", back_populates="references")


class GenomeMap(BaseModel):
    """BrAPI Genome Map - A genetic or physical map"""

    __tablename__ = "genome_maps"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    map_db_id = Column(String(255), unique=True, index=True)
    map_name = Column(String(255), nullable=False, index=True)
    map_pui = Column(String(255))
    common_crop_name = Column(String(100))
    type = Column(String(50))  # genetic, physical
    unit = Column(String(20))  # cM, bp
    scientific_name = Column(String(255))
    published_date = Column(String(50))
    comments = Column(Text)
    documentation_url = Column(Text)
    linkage_group_count = Column(Integer)
    marker_count = Column(Integer)

    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)

    # Relationships
    organization = relationship("Organization")
    linkage_groups = relationship("LinkageGroup", back_populates="genome_map", cascade="all, delete-orphan")
    marker_positions = relationship("MarkerPosition", back_populates="genome_map", cascade="all, delete-orphan")


class LinkageGroup(BaseModel):
    """BrAPI Linkage Group - A chromosome or linkage group in a map"""

    __tablename__ = "linkage_groups"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    map_id = Column(Integer, ForeignKey("genome_maps.id"), nullable=False, index=True)

    linkage_group_name = Column(String(100), nullable=False, index=True)
    max_position = Column(Float)
    marker_count = Column(Integer)

    # BrAPI additional info
    additional_info = Column(JSON)

    # Relationships
    organization = relationship("Organization")
    genome_map = relationship("GenomeMap", back_populates="linkage_groups")


class MarkerPosition(BaseModel):
    """BrAPI Marker Position - Position of a marker on a map"""

    __tablename__ = "marker_positions"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    map_id = Column(Integer, ForeignKey("genome_maps.id"), nullable=False, index=True)

    marker_position_db_id = Column(String(255), unique=True, index=True)
    variant_db_id = Column(String(255), index=True)
    variant_name = Column(String(255), index=True)
    linkage_group_name = Column(String(100), index=True)
    position = Column(Float)

    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)

    # Relationships
    organization = relationship("Organization")
    genome_map = relationship("GenomeMap", back_populates="marker_positions")


class VariantSet(BaseModel):
    """BrAPI Variant Set - A set of variants (VCF file equivalent)"""

    __tablename__ = "variant_sets"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    reference_set_id = Column(Integer, ForeignKey("reference_sets.id"), index=True)
    study_id = Column(Integer, ForeignKey("studies.id"), index=True)

    variant_set_db_id = Column(String(255), unique=True, index=True)
    variant_set_name = Column(String(255), nullable=False, index=True)
    analysis = Column(JSON)  # List of analysis objects
    available_formats = Column(JSON)  # List of format objects
    call_set_count = Column(Integer)
    variant_count = Column(Integer)

    # Storage optimization
    storage_path = Column(String(512)) # Path to Zarr/HDF5 on disk

    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)

    # Relationships
    organization = relationship("Organization")
    reference_set = relationship("ReferenceSet")
    study = relationship("Study")
    variants = relationship("Variant", back_populates="variant_set", cascade="all, delete-orphan")
    call_sets = relationship("CallSet", secondary="variant_set_call_sets", back_populates="variant_sets")


class Variant(BaseModel):
    """BrAPI Variant - A genetic variant (SNP, indel, etc.)"""

    __tablename__ = "variants"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    variant_set_id = Column(Integer, ForeignKey("variant_sets.id"), index=True)
    reference_id = Column(Integer, ForeignKey("references.id"), index=True)

    variant_db_id = Column(String(255), unique=True, index=True)
    variant_name = Column(String(255), index=True)
    variant_type = Column(String(50))  # SNP, MNP, INDEL, etc.
    reference_bases = Column(Text)
    alternate_bases = Column(JSON)  # List of alternate allele strings
    start = Column(Integer, index=True)
    end = Column(Integer)
    cipos = Column(JSON)  # Confidence interval around start
    ciend = Column(JSON)  # Confidence interval around end
    svlen = Column(Integer)  # Structural variant length
    filters_applied = Column(Boolean, default=True)
    filters_passed = Column(Boolean)

    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)

    # Relationships
    organization = relationship("Organization")
    variant_set = relationship("VariantSet", back_populates="variants")
    reference = relationship("Reference")
    calls = relationship("Call", back_populates="variant", cascade="all, delete-orphan")


class CallSet(BaseModel):
    """BrAPI Call Set - A set of calls for a sample (genotype data for one individual)"""

    __tablename__ = "call_sets"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    sample_id = Column(Integer, ForeignKey("samples.id"), index=True)

    call_set_db_id = Column(String(255), unique=True, index=True)
    call_set_name = Column(String(255), nullable=False, index=True)
    sample_db_id = Column(String(255), index=True)
    created = Column(String(50))
    updated = Column(String(50))

    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)

    # Relationships
    organization = relationship("Organization")
    sample = relationship("Sample")
    calls = relationship("Call", back_populates="call_set", cascade="all, delete-orphan")
    variant_sets = relationship("VariantSet", secondary="variant_set_call_sets", back_populates="call_sets")


# Association table for VariantSet <-> CallSet many-to-many
from sqlalchemy import Table
variant_set_call_sets = Table(
    'variant_set_call_sets',
    BaseModel.metadata,
    Column('variant_set_id', Integer, ForeignKey('variant_sets.id'), primary_key=True),
    Column('call_set_id', Integer, ForeignKey('call_sets.id'), primary_key=True)
)


class Call(BaseModel):
    """BrAPI Call - A genotype call for a variant in a call set"""

    __tablename__ = "calls"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("variants.id"), nullable=False, index=True)
    call_set_id = Column(Integer, ForeignKey("call_sets.id"), nullable=False, index=True)

    call_db_id = Column(String(255), unique=True, index=True)
    genotype = Column(JSON)  # Genotype object with values, metadata
    genotype_value = Column(String(50))  # Simplified genotype string (e.g., "0/1")
    genotype_likelihood = Column(JSON)  # List of likelihoods
    phaseSet = Column(String(255))

    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)

    # Relationships
    organization = relationship("Organization")
    variant = relationship("Variant", back_populates="calls")
    call_set = relationship("CallSet", back_populates="calls")


class Plate(BaseModel):
    """BrAPI Plate - A physical plate for genotyping samples"""

    __tablename__ = "plates"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"), index=True)
    trial_id = Column(Integer, ForeignKey("trials.id"), index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), index=True)

    plate_db_id = Column(String(255), unique=True, index=True)
    plate_name = Column(String(255), nullable=False, index=True)
    plate_barcode = Column(String(255), index=True)
    plate_format = Column(String(50))  # PLATE_96, PLATE_384, TUBES
    sample_type = Column(String(100))
    status_time_stamp = Column(String(50))
    client_plate_db_id = Column(String(255))
    client_plate_barcode = Column(String(255))

    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)

    # Relationships
    organization = relationship("Organization")
    study = relationship("Study")
    trial = relationship("Trial")
    program = relationship("Program")


class VendorOrder(BaseModel):
    """BrAPI Vendor Order - An order for genotyping services"""

    __tablename__ = "vendor_orders"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    order_db_id = Column(String(255), unique=True, index=True)
    client_id = Column(String(255), index=True)
    number_of_samples = Column(Integer)
    order_id = Column(String(255))
    required_service_info = Column(JSON)
    service_ids = Column(JSON)  # List of service IDs
    status = Column(String(50))  # REGISTERED, RECEIVED, INPROGRESS, COMPLETED
    status_time_stamp = Column(String(50))

    # BrAPI additional info
    additional_info = Column(JSON)
    external_references = Column(JSON)

    # Relationships
    organization = relationship("Organization")
