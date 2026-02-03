"""
Phenomic Selection Models

Database models for phenomic selection and high-throughput phenotyping.
Supports NIRS, hyperspectral imaging, thermal imaging, and other spectral platforms.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, Index, Date, JSON
)
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class PhenomicDataset(BaseModel):
    """
    Phenomic Dataset - High-throughput phenotyping spectral data collection.
    
    Stores metadata about spectral datasets from various platforms
    (NIRS, hyperspectral, thermal imaging, etc.).
    """
    
    __tablename__ = "phenomic_datasets"
    
    # Core identifiers
    dataset_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Crop and platform
    crop = Column(String(100), nullable=False, index=True)
    platform = Column(String(100), nullable=False, index=True)  # NIRS, Hyperspectral, Thermal, etc.
    
    # Dataset metrics
    samples = Column(Integer, nullable=False, default=0)
    wavelengths = Column(Integer, nullable=False, default=0)  # Number of spectral bands
    
    # Traits that can be predicted from this dataset
    traits_predicted = Column(JSON)  # List of trait names
    
    # Quality metrics
    accuracy = Column(Float)  # Overall prediction accuracy
    
    # Status
    status = Column(String(20), nullable=False, default="active", index=True)
    
    # Notes
    description = Column(Text)
    notes = Column(Text)
    
    # Organization (multi-tenant)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Relationships
    organization = relationship("Organization")
    models = relationship("PhenomicModel", back_populates="dataset")
    
    def __repr__(self):
        return f"<PhenomicDataset {self.dataset_code}: {self.name}>"


class PhenomicModel(BaseModel):
    """
    Phenomic Model - Prediction model trained on spectral data.
    
    Supports various model types: PLSR, Random Forest, Deep Learning, etc.
    """
    
    __tablename__ = "phenomic_models"
    
    # Core identifiers
    model_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Model type
    model_type = Column(String(100), nullable=False)  # PLSR, Random Forest, Deep Learning, etc.
    
    # Dataset reference
    dataset_id = Column(Integer, ForeignKey("phenomic_datasets.id"), nullable=False, index=True)
    
    # Target trait
    target_trait = Column(String(255), nullable=False)
    
    # Performance metrics (varies by model type)
    r_squared = Column(Float)  # Coefficient of determination
    rmse = Column(Float)  # Root mean square error
    accuracy = Column(Float)  # For classification models
    f1_score = Column(Float)  # For classification models
    
    # Model parameters (stored as JSON for flexibility)
    parameters = Column(JSON)  # e.g., {"components": 12} for PLSR, {"n_estimators": 500} for RF
    
    # Status
    status = Column(String(20), nullable=False, default="training", index=True)  # training, deployed, archived
    
    # Notes
    description = Column(Text)
    notes = Column(Text)
    
    # Organization (multi-tenant)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Relationships
    organization = relationship("Organization")
    dataset = relationship("PhenomicDataset", back_populates="models")
    
    __table_args__ = (
        Index('ix_phenomic_models_dataset_status', 'dataset_id', 'status'),
    )
    
    def __repr__(self):
        return f"<PhenomicModel {self.model_code}: {self.name}>"
