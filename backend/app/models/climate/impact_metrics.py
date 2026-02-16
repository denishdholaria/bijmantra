"""
Impact Metrics & Reporting Models

Tracks sustainability impact and policy influence for reporting.

Scientific Basis:
    Sustainability Metrics:
        - Hectares impacted: Area under improved varieties
        - Farmers reached: Direct + indirect beneficiaries
        - Yield improvement: % increase over baseline
        - Climate resilience: Stress tolerance indicators
    
    UN Sustainable Development Goals (SDGs):
        - SDG 2: Zero Hunger
        - SDG 13: Climate Action
        - SDG 15: Life on Land
        - SDG 17: Partnerships for the Goals
"""

import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Date, Enum, JSON, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class MetricType(str, enum.Enum):
    """Type of impact metric"""
    HECTARES = "hectares"
    FARMERS = "farmers"
    YIELD_IMPROVEMENT = "yield_improvement"
    CLIMATE_RESILIENCE = "climate_resilience"
    CARBON_SEQUESTERED = "carbon_sequestered"
    EMISSIONS_REDUCED = "emissions_reduced"
    BIODIVERSITY = "biodiversity"
    WATER_SAVED = "water_saved"
    ECONOMIC = "economic"
    OTHER = "other"


class SDGGoal(str, enum.Enum):
    """UN Sustainable Development Goals"""
    SDG_1 = "sdg_1_no_poverty"
    SDG_2 = "sdg_2_zero_hunger"
    SDG_3 = "sdg_3_good_health"
    SDG_6 = "sdg_6_clean_water"
    SDG_7 = "sdg_7_clean_energy"
    SDG_8 = "sdg_8_decent_work"
    SDG_9 = "sdg_9_industry_innovation"
    SDG_12 = "sdg_12_responsible_consumption"
    SDG_13 = "sdg_13_climate_action"
    SDG_15 = "sdg_15_life_on_land"
    SDG_17 = "sdg_17_partnerships"


class ReleaseStatus(str, enum.Enum):
    """Variety release status"""
    PENDING = "pending"
    APPROVED = "approved"
    RELEASED = "released"
    WITHDRAWN = "withdrawn"


class AdoptionLevel(str, enum.Enum):
    """Policy adoption level"""
    PILOT = "pilot"
    REGIONAL = "regional"
    NATIONAL = "national"
    INTERNATIONAL = "international"


class ImpactMetric(BaseModel):
    """
    Sustainability impact metrics.
    
    Tracks quantifiable sustainability outcomes from breeding programs.
    
    Attributes:
        organization_id: Multi-tenant isolation (RLS)
        program_id: Reference to breeding program
        metric_type: Type of impact metric
        metric_name: Descriptive name
        metric_value: Quantitative value
        unit: Unit of measurement
        baseline_value: Baseline for comparison
        measurement_date: Date of measurement
        geographic_scope: Geographic area (country, region, etc.)
        beneficiaries: Number of direct beneficiaries
        notes: Additional context
    """

    __tablename__ = "impact_metrics"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True, index=True)

    metric_type = Column(Enum(MetricType), nullable=False, index=True)
    metric_name = Column(String(255), nullable=False)

    # Metric value
    metric_value = Column(Float, nullable=False)
    unit = Column(String(100), nullable=False)
    baseline_value = Column(Float, nullable=True)

    # Context
    measurement_date = Column(Date, nullable=False, index=True)
    geographic_scope = Column(String(255), nullable=True)
    beneficiaries = Column(Integer, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Relationships
    organization = relationship("Organization")
    program = relationship("Program")


class SDGIndicator(BaseModel):
    """
    UN SDG alignment indicators.
    
    Maps breeding program outcomes to UN Sustainable Development Goals.
    
    Attributes:
        organization_id: Multi-tenant isolation (RLS)
        program_id: Reference to breeding program
        sdg_goal: UN SDG goal
        indicator_code: Official SDG indicator code (e.g., "2.3.1")
        indicator_name: Indicator description
        contribution_value: Quantitative contribution
        unit: Unit of measurement
        measurement_date: Date of measurement
        evidence: Supporting evidence (JSON)
        notes: Additional context
    """

    __tablename__ = "sdg_indicators"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True, index=True)

    sdg_goal = Column(Enum(SDGGoal), nullable=False, index=True)
    indicator_code = Column(String(50), nullable=True)
    indicator_name = Column(String(500), nullable=False)

    # Contribution
    contribution_value = Column(Float, nullable=False)
    unit = Column(String(100), nullable=False)
    measurement_date = Column(Date, nullable=False, index=True)

    # Evidence
    evidence = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    organization = relationship("Organization")
    program = relationship("Program")


class VarietyRelease(BaseModel):
    """
    Official variety releases and registrations.
    
    Tracks varieties released through official channels (government, seed companies).
    
    Attributes:
        organization_id: Multi-tenant isolation (RLS)
        germplasm_id: Reference to variety
        program_id: Reference to breeding program
        release_name: Official release name
        release_date: Date of official release
        release_status: Current status
        country: Country of release
        region: Region/state of release
        releasing_authority: Government body or organization
        registration_number: Official registration number
        target_environment: Target production environment
        expected_adoption_ha: Expected adoption area (hectares)
        actual_adoption_ha: Actual adoption area (hectares)
        documentation_url: Link to official documentation
        notes: Additional notes
    """

    __tablename__ = "variety_releases"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    germplasm_id = Column(Integer, ForeignKey("germplasm.id"), nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True, index=True)

    release_name = Column(String(255), nullable=False)
    release_date = Column(Date, nullable=False, index=True)
    release_status = Column(Enum(ReleaseStatus), nullable=False, default=ReleaseStatus.PENDING)

    # Geographic scope
    country = Column(String(100), nullable=False)
    region = Column(String(255), nullable=True)

    # Authority
    releasing_authority = Column(String(255), nullable=False)
    registration_number = Column(String(100), nullable=True)

    # Target and adoption
    target_environment = Column(String(500), nullable=True)
    expected_adoption_ha = Column(Float, nullable=True)
    actual_adoption_ha = Column(Float, nullable=True)

    # Documentation
    documentation_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    organization = relationship("Organization")
    germplasm = relationship("Germplasm")
    program = relationship("Program")


class PolicyAdoption(BaseModel):
    """
    Government policy adoptions.
    
    Tracks adoption of varieties or practices in government programs.
    
    Attributes:
        organization_id: Multi-tenant isolation (RLS)
        program_id: Reference to breeding program
        germplasm_id: Reference to variety (optional)
        policy_name: Name of government program/policy
        adoption_date: Date of adoption
        adoption_level: Geographic level
        country: Country
        region: Region/state
        government_body: Responsible government agency
        budget_allocated: Budget allocated (if known)
        currency: Currency of budget
        target_farmers: Target number of farmers
        target_hectares: Target area (hectares)
        description: Policy description
        documentation_url: Link to policy document
        notes: Additional notes
    """

    __tablename__ = "policy_adoptions"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True, index=True)
    germplasm_id = Column(Integer, ForeignKey("germplasm.id"), nullable=True, index=True)

    policy_name = Column(String(500), nullable=False)
    adoption_date = Column(Date, nullable=False, index=True)
    adoption_level = Column(Enum(AdoptionLevel), nullable=False)

    # Geographic scope
    country = Column(String(100), nullable=False)
    region = Column(String(255), nullable=True)
    government_body = Column(String(255), nullable=False)

    # Budget and targets
    budget_allocated = Column(Float, nullable=True)
    currency = Column(String(10), nullable=True)
    target_farmers = Column(Integer, nullable=True)
    target_hectares = Column(Float, nullable=True)

    # Description
    description = Column(Text, nullable=True)
    documentation_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    organization = relationship("Organization")
    program = relationship("Program")
    germplasm = relationship("Germplasm")


class Publication(BaseModel):
    """
    Research publications citing BijMantra.
    
    Tracks scientific publications that use BijMantra data or cite the platform.
    
    Attributes:
        organization_id: Multi-tenant isolation (RLS)
        program_id: Reference to breeding program
        title: Publication title
        authors: Author list
        journal: Journal name
        publication_date: Date of publication
        doi: Digital Object Identifier
        url: Publication URL
        citation_count: Number of citations (if known)
        impact_factor: Journal impact factor (if known)
        abstract: Publication abstract
        keywords: Keywords (JSON array)
        bijmantra_usage: How BijMantra was used
        notes: Additional notes
    """

    __tablename__ = "publications"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True, index=True)

    title = Column(String(1000), nullable=False)
    authors = Column(Text, nullable=False)
    journal = Column(String(500), nullable=True)
    publication_date = Column(Date, nullable=False, index=True)

    # Identifiers
    doi = Column(String(255), nullable=True)
    url = Column(String(500), nullable=True)

    # Metrics
    citation_count = Column(Integer, nullable=True)
    impact_factor = Column(Float, nullable=True)

    # Content
    abstract = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)
    bijmantra_usage = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    organization = relationship("Organization")
    program = relationship("Program")


class ImpactReport(BaseModel):
    """
    Generated impact reports.
    
    Stores generated sustainability and impact reports.
    
    Attributes:
        organization_id: Multi-tenant isolation (RLS)
        program_id: Reference to breeding program
        report_title: Report title
        report_type: Type of report (annual, donor, GEE, custom)
        reporting_period_start: Start date of reporting period
        reporting_period_end: End date of reporting period
        generated_date: Date report was generated
        generated_by_user_id: User who generated report
        report_data: Report data (JSON)
        file_url: URL to generated report file
        format: Report format (PDF, DOCX, HTML)
        notes: Additional notes
    """

    __tablename__ = "impact_reports"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True, index=True)

    report_title = Column(String(500), nullable=False)
    report_type = Column(String(100), nullable=False)  # annual, donor, gee_partner, custom

    # Reporting period
    reporting_period_start = Column(Date, nullable=False)
    reporting_period_end = Column(Date, nullable=False)

    # Generation metadata
    generated_date = Column(Date, nullable=False, index=True)
    generated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Report content
    report_data = Column(JSON, nullable=False)
    file_url = Column(String(500), nullable=True)
    format = Column(String(50), nullable=False)  # PDF, DOCX, HTML

    # Notes
    notes = Column(Text, nullable=True)

    # Relationships
    organization = relationship("Organization")
    program = relationship("Program")
    generated_by = relationship("User", foreign_keys=[generated_by_user_id])
