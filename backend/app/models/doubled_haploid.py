"""
Doubled Haploid Models

Database models for DH (Doubled Haploid) production and management.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, Index, Date
)
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class DHProtocol(BaseModel):
    """
    DH Protocol - Doubled haploid production protocol.
    
    Defines the method, rates, and parameters for DH line production.
    """

    __tablename__ = "dh_protocols"

    # Core identifiers
    protocol_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)

    # Crop and method
    crop = Column(String(100), nullable=False, index=True)
    method = Column(String(100), nullable=False)  # anther culture, microspore culture, in vivo maternal

    # Induction parameters
    inducer = Column(String(255))  # e.g., "Stock 6 derivatives" for maize
    induction_rate = Column(Float, nullable=False, default=0.1)  # Proportion of haploids induced

    # Doubling parameters
    doubling_agent = Column(String(100))  # Colchicine, Spontaneous, etc.
    doubling_rate = Column(Float, nullable=False, default=0.25)  # Proportion successfully doubled

    # Efficiency
    overall_efficiency = Column(Float)  # induction_rate * doubling_rate
    days_to_complete = Column(Integer)  # Typical duration

    # Status
    status = Column(String(20), nullable=False, default="active", index=True)

    # Notes
    notes = Column(Text)

    # Organization (multi-tenant)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Relationships
    organization = relationship("Organization")
    batches = relationship("DHBatch", back_populates="protocol")

    def __repr__(self):
        return f"<DHProtocol {self.protocol_code}: {self.name}>"


class DHBatch(BaseModel):
    """
    DH Batch - A batch of doubled haploid production.
    
    Tracks the progress of DH line production from donor plants to fertile lines.
    """

    __tablename__ = "dh_batches"

    # Core identifiers
    batch_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)

    # Protocol reference
    protocol_id = Column(Integer, ForeignKey("dh_protocols.id"), nullable=False, index=True)

    # Donor information
    donor_cross = Column(String(255))  # e.g., "B73 x Mo17"
    donor_plants = Column(Integer, nullable=False, default=0)

    # Production tracking (varies by method)
    # For anther/microspore culture:
    anthers_cultured = Column(Integer)
    embryos_formed = Column(Integer)
    plants_regenerated = Column(Integer)

    # For in vivo methods:
    haploids_induced = Column(Integer)
    haploids_identified = Column(Integer)
    doubled_plants = Column(Integer)

    # Final output
    fertile_dh_lines = Column(Integer, default=0)

    # Progress tracking
    stage = Column(String(100))  # Current stage in workflow
    start_date = Column(Date)
    end_date = Column(Date)

    # Status
    status = Column(String(20), nullable=False, default="active", index=True)

    # Notes
    notes = Column(Text)

    # Organization (multi-tenant)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Relationships
    organization = relationship("Organization")
    protocol = relationship("DHProtocol", back_populates="batches")

    __table_args__ = (
        Index('ix_dh_batches_protocol_status', 'protocol_id', 'status'),
    )

    def __repr__(self):
        return f"<DHBatch {self.batch_code}: {self.name}>"
