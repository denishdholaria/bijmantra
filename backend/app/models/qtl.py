"""
QTL Mapping and Gene Ontology Models
"""

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


# Association table for Gene-GOTerm many-to-many
gene_go_terms = Table(
    "gene_go_terms",
    BaseModel.metadata,
    Column("gene_id", Integer, ForeignKey("genes.id"), primary_key=True),
    Column("go_term_id", Integer, ForeignKey("go_terms.id"), primary_key=True),
)

class QTL(BaseModel):
    """Quantitative Trait Locus"""
    __tablename__ = "qtls"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    trait = Column(String(255), nullable=False, index=True)
    chromosome = Column(String(50), nullable=False, index=True)
    position = Column(Float, nullable=False)
    start_position = Column(Float)  # CI start
    end_position = Column(Float)    # CI end
    lod = Column(Float)
    pve = Column(Float)             # Phenotypic Variance Explained
    population = Column(String(255))

    organization = relationship("Organization")

class Gene(BaseModel):
    """Gene annotation"""
    __tablename__ = "genes"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    gene_id = Column(String(255), unique=True, index=True)
    name = Column(String(255), index=True)
    chromosome = Column(String(50), index=True)
    start = Column(Integer, index=True)
    end = Column(Integer, index=True)
    strand = Column(String(1))
    description = Column(Text)

    organization = relationship("Organization")
    go_terms = relationship("GOTerm", secondary=gene_go_terms, back_populates="genes")

class GOTerm(BaseModel):
    """Gene Ontology Term"""
    __tablename__ = "go_terms"

    go_id = Column(String(50), unique=True, index=True)  # GO:XXXXXXX
    term = Column(String(255), index=True)
    category = Column(String(50))  # biological_process, molecular_function, cellular_component
    definition = Column(Text)

    genes = relationship("Gene", secondary=gene_go_terms, back_populates="go_terms")
