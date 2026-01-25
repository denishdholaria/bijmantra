"""
Dispatch and Firm Models

Database models for seed dispatch management and firm/dealer tracking.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, Index
)
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Firm(BaseModel):
    """
    Firm - Dealers, distributors, retailers, and other business entities.
    
    Used for tracking seed dispatch recipients and business relationships.
    """
    
    __tablename__ = "firms"
    
    # Core identifiers
    firm_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Classification
    firm_type = Column(String(50), nullable=False, index=True)  # dealer, distributor, retailer, farmer, institution, government
    status = Column(String(20), nullable=False, default="active", index=True)
    
    # Address
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Contact
    contact_person = Column(String(255))
    phone = Column(String(50))
    email = Column(String(255))
    
    # Business details
    gst_number = Column(String(50))  # Tax ID
    credit_limit = Column(Float, nullable=False, default=0)
    credit_used = Column(Float, nullable=False, default=0)
    
    # Notes
    notes = Column(Text)
    
    # Organization (multi-tenant)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Relationships
    organization = relationship("Organization")
    dispatches = relationship("Dispatch", back_populates="recipient_firm")
    
    __table_args__ = (
        Index('ix_firms_city_state', 'city', 'state'),
    )
    
    def __repr__(self):
        return f"<Firm {self.firm_code}: {self.name}>"


class Dispatch(BaseModel):
    """
    Dispatch - Seed dispatch order for tracking shipments.
    
    Tracks the full lifecycle from draft to delivery.
    """
    
    __tablename__ = "dispatches"
    
    # Core identifiers
    dispatch_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Recipient (can be linked to Firm or ad-hoc)
    recipient_id = Column(Integer, ForeignKey("firms.id"), nullable=True, index=True)
    recipient_name = Column(String(255), nullable=False)
    recipient_address = Column(Text)
    recipient_contact = Column(String(255))
    recipient_phone = Column(String(50))
    
    # Transfer details
    transfer_type = Column(String(50), nullable=False, index=True)  # sale, internal, donation, sample, return
    total_quantity_kg = Column(Float, nullable=False, default=0)
    total_value = Column(Float, nullable=False, default=0)
    
    # Status workflow
    status = Column(String(50), nullable=False, default="draft", index=True)
    # Statuses: draft, pending_approval, approved, picking, packed, shipped, in_transit, delivered, cancelled
    
    # Audit trail
    created_by = Column(String(255))
    approved_at = Column(DateTime(timezone=True))
    approved_by = Column(String(255))
    shipped_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    
    # Shipping details
    tracking_number = Column(String(100))
    carrier = Column(String(100))
    invoice_number = Column(String(100))
    
    # Notes
    notes = Column(Text)
    
    # Organization (multi-tenant)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Relationships
    organization = relationship("Organization")
    recipient_firm = relationship("Firm", back_populates="dispatches")
    items = relationship("DispatchItem", back_populates="dispatch", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_dispatches_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Dispatch {self.dispatch_number}: {self.status}>"


class DispatchItem(BaseModel):
    """
    DispatchItem - Line item in a dispatch order.
    
    Links to seedlots and tracks picking/packing status.
    """
    
    __tablename__ = "dispatch_items"
    
    # Parent dispatch
    dispatch_id = Column(Integer, ForeignKey("dispatches.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Seedlot reference (optional FK)
    seedlot_id = Column(Integer, ForeignKey("seedlots.id"), nullable=True, index=True)
    lot_id = Column(String(100), nullable=False)  # External lot reference
    
    # Product details
    variety_name = Column(String(255))
    crop = Column(String(100))
    seed_class = Column(String(50))  # breeder, foundation, certified, truthful
    
    # Quantity and pricing
    quantity_kg = Column(Float, nullable=False)
    unit_price = Column(Float)
    total_price = Column(Float)
    
    # Fulfillment status
    picked = Column(Boolean, nullable=False, default=False)
    packed = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    dispatch = relationship("Dispatch", back_populates="items")
    seedlot = relationship("Seedlot")
    
    def __repr__(self):
        return f"<DispatchItem {self.lot_id}: {self.quantity_kg}kg>"
