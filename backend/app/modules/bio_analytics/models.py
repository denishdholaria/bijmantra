from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.models.base import BaseModel

class GSModel(BaseModel):
    """
    Genomic Selection Model Metadata.
    Stores information about trained models.
    """
    __tablename__ = "bio_gs_models"
    __table_args__ = {'extend_existing': True}

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Model Identification
    model_name = Column(String(255), nullable=False)
    trait_name = Column(String(255), nullable=False, index=True)
    method = Column(String(50), nullable=False) # GBLUP, BayesB, RR-BLUP
    
    # Training Metadata
    training_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    training_population_size = Column(Integer)
    marker_count = Column(Integer)
    
    # Validation Metrics
    accuracy = Column(Float) # Cross-validation accuracy (r)
    heritability = Column(Float)
    genetic_variance = Column(Float)
    error_variance = Column(Float)
    
    # Status
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Relationships
    organization = relationship("Organization")
    marker_effects = relationship("MarkerEffect", back_populates="model", cascade="all, delete-orphan")
    predictions = relationship("GEBVPrediction", back_populates="model", cascade="all, delete-orphan")


class MarkerEffect(BaseModel):
    """
    Marker Effects for a specific GS Model.
    Used for predicting GEBVs of new genotypes.
    """
    __tablename__ = "bio_marker_effects"
    __table_args__ = {'extend_existing': True}
    
    organization_id = Column(Integer, nullable=False, index=True) # Data Isolation
    model_id = Column(Integer, ForeignKey("bio_gs_models.id"), nullable=False, index=True)
    
    marker_name = Column(String(255), nullable=False, index=True)
    chromosome = Column(String(50))
    position = Column(Integer)
    effect = Column(Float, nullable=False)
    
    # Relationships
    model = relationship("GSModel", back_populates="marker_effects")


class GEBVPrediction(BaseModel):
    """
    Genomic Estimated Breeding Values (GEBVs).
    Stores prediction results for germplasm.
    """
    __tablename__ = "bio_gebv_predictions"
    __table_args__ = {'extend_existing': True}
    
    organization_id = Column(Integer, nullable=False, index=True) # Data Isolation
    model_id = Column(Integer, ForeignKey("bio_gs_models.id"), nullable=False, index=True)
    germplasm_id = Column(String(255), nullable=False, index=True) # Linking to germplasm_db_id
    
    gebv = Column(Float, nullable=False)
    reliability = Column(Float)
    
    predicted_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    model = relationship("GSModel", back_populates="predictions")


class GWASRun(BaseModel):
    """
    Metadata for a Genome-Wide Association Study run.
    """
    __tablename__ = "bio_gwas_runs"
    __table_args__ = {'extend_existing': True}

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    run_name = Column(String(255), nullable=False)
    trait_name = Column(String(255), nullable=False, index=True)
    method = Column(String(50), nullable=False) # GLM, MLM
    
    run_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    sample_size = Column(Integer)
    marker_count = Column(Integer)
    
    # Results Summary
    significance_threshold = Column(Float)
    significant_marker_count = Column(Integer, default=0)
    
    # JSON Blobs for Visualization (Manhattan/QQ Plots)
    # Storing these as JSON avoids saving millions of rows for non-significant markers
    manhattan_plot_data = Column(JSON) 
    qq_plot_data = Column(JSON)
    
    organization = relationship("Organization")
    results = relationship("GWASResult", back_populates="run", cascade="all, delete-orphan")


class GWASResult(BaseModel):
    """
    Significant marker associations from a GWAS run.
    Only stores markers passing a relaxed threshold to save space.
    """
    __tablename__ = "bio_gwas_results"
    __table_args__ = {'extend_existing': True}
    
    organization_id = Column(Integer, nullable=False, index=True) # Data Isolation
    run_id = Column(Integer, ForeignKey("bio_gwas_runs.id"), nullable=False, index=True)
    
    marker_name = Column(String(255), nullable=False, index=True)
    chromosome = Column(String(50))
    position = Column(Integer)
    
    p_value = Column(Float, nullable=False)
    neg_log10_p = Column(Float)
    effect_size = Column(Float)
    standard_error = Column(Float)
    maf = Column(Float)
    
    is_significant = Column(Boolean, default=False)
    
    run = relationship("GWASRun", back_populates="results")
