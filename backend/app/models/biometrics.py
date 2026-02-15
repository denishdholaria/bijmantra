"""
Biometrics & Analytics Models
Genomic Selection Models, Stability Analysis Results, and Cross Predictions
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import BaseModel


class BiometricsGSModel(BaseModel):
    """Genomic Selection Model - A trained model for GEBV prediction"""
    
    __tablename__ = "gs_models"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Model Metadata
    model_db_id = Column(String(255), unique=True, index=True)
    model_name = Column(String(255), nullable=False, index=True)
    trait_name = Column(String(255), nullable=False, index=True) # Target trait
    method = Column(String(50), nullable=False) # GBLUP, rrBLUP, BayesB, etc.
    engine = Column(String(50), default="sklearn") # sklearn, torch, etc.
    
    # Training Config
    training_population_size = Column(Integer)
    marker_count = Column(Integer)
    cv_folds = Column(Integer, default=5)
    training_set_ids = Column(JSON) # List of germplasm IDs used for training
    
    # Model Performance
    accuracy = Column(Float) # Cross-validation accuracy (r)
    heritability = Column(Float) # Narrow-sense heritability (h^2)
    genetic_variance = Column(Float)
    error_variance = Column(Float)
    metrics = Column(JSON) # Detailed metrics (MSE, MAE, etc.)
    
    # Storage
    file_path = Column(String(512)) # Path to serialized `.surml` or `.pkl` file
    status = Column(String(50), default="TRAINING") # TRAINING, COMPLETED, FAILED
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")


class StabilityResult(BaseModel):
    """Stability Analysis Result - Stability metrics for a single germplasm"""
    
    __tablename__ = "stability_results"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    germplasm_id = Column(Integer, ForeignKey("germplasm.id"), nullable=False, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"), index=True) # Optional: if linked to a specific MET study
    
    # Analysis Context
    method = Column(String(50), nullable=False) # Eberhart-Russell, AMMI, etc.
    environments_tested = Column(Integer)
    years_tested = Column(Integer)
    
    # Metrics (Generic retrieval via JSON, specific columns for indexing)
    mean_yield = Column(Float)
    slope = Column(Float) # bi (Eberhart-Russell)
    deviation = Column(Float) # S2di
    stability_variance = Column(Float) # Shukla's sigma^2
    wricke_ecovalence = Column(Float) # Wi
    ammi_asv = Column(Float) # AMMI Stability Value
    lin_binns_pi = Column(Float) # Pi
    
    ranking = Column(Integer) # Rank within the analysis set
    classification = Column(String(50)) # STABLE, RESPONSIVE, SENSITIVE
    
    raw_data = Column(JSON) # Full results payload
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    organization = relationship("Organization")
    germplasm = relationship("Germplasm")
    study = relationship("Study")


class CrossPredictionResult(BaseModel):
    """Cross Prediction Result - Predicted performance of a specific cross"""
    
    __tablename__ = "cross_predictions"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Parents
    parent1_id = Column(Integer, ForeignKey("germplasm.id"), nullable=False, index=True)
    parent2_id = Column(Integer, ForeignKey("germplasm.id"), nullable=False, index=True)
    
    # Prediction
    predicted_mean = Column(Float)
    predicted_variance = Column(Float)
    usefulness_criterion = Column(Float) # U = mean + i * sd
    superiority_prob = Column(Float) # P(progeny > threshold)
    
    # Genetics
    genetic_distance = Column(Float)
    inbreeding_coeff = Column(Float)
    
    # Metadata
    model_id = Column(Integer, ForeignKey("gs_models.id")) # Model used for prediction
    trait_name = Column(String(255))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    organization = relationship("Organization")
    parent1 = relationship("Germplasm", foreign_keys=[parent1_id])
    parent2 = relationship("Germplasm", foreign_keys=[parent2_id])
    model = relationship("BiometricsGSModel")
