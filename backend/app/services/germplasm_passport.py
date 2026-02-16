"""
Germplasm Passport Service for Plant Breeding
FAO/IPGRI Multi-Crop Passport Descriptors (MCPD) compliant

Features:
- Passport data management
- Collection site recording
- Biological status tracking
- Acquisition and distribution
- MCPD export
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BiologicalStatus(str, Enum):
    WILD = "100"
    WEEDY = "200"
    LANDRACE = "300"
    BREEDING_LINE = "400"
    ADVANCED_CULTIVAR = "500"
    GMO = "600"
    OTHER = "999"


class SampleType(str, Enum):
    SEED = "seed"
    VEGETATIVE = "vegetative"
    DNA = "dna"
    TISSUE = "tissue"


class AcquisitionSource(str, Enum):
    WILD = "10"
    FARM = "20"
    MARKET = "30"
    INSTITUTE = "40"
    SEED_COMPANY = "50"
    OTHER = "99"


@dataclass
class CollectionSite:
    """Collection site information"""
    country: str  # ISO 3166-1 alpha-3
    state_province: str
    municipality: str
    locality: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation: Optional[float] = None  # meters
    collection_date: Optional[date] = None
    collector_name: str = ""
    collector_institute: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "country_code": self.country,
            "state_province": self.state_province,
            "municipality": self.municipality,
            "locality": self.locality,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "elevation_m": self.elevation,
            "collection_date": self.collection_date.isoformat() if self.collection_date else None,
            "collector_name": self.collector_name,
            "collector_institute": self.collector_institute,
        }


@dataclass
class GermplasmPassport:
    """MCPD-compliant germplasm passport"""
    accession_id: str  # ACCENUMB
    accession_name: str  # ACCENAME
    genus: str  # GENUS
    species: str  # SPECIES
    species_authority: str = ""  # SPAUTHOR
    subtaxa: str = ""  # SUBTAXA
    common_name: str = ""
    biological_status: BiologicalStatus = BiologicalStatus.OTHER
    sample_type: SampleType = SampleType.SEED
    acquisition_source: AcquisitionSource = AcquisitionSource.OTHER
    acquisition_date: Optional[date] = None
    donor_institute: str = ""
    donor_accession: str = ""
    collection_site: Optional[CollectionSite] = None
    pedigree: str = ""
    remarks: str = ""
    storage_location: str = ""
    mlsstat: str = ""  # MLS status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accession_id": self.accession_id,
            "accession_name": self.accession_name,
            "taxonomy": {
                "genus": self.genus,
                "species": self.species,
                "species_authority": self.species_authority,
                "subtaxa": self.subtaxa,
                "full_name": f"{self.genus} {self.species}" + (f" {self.subtaxa}" if self.subtaxa else ""),
            },
            "common_name": self.common_name,
            "biological_status": self.biological_status.value,
            "biological_status_name": self._get_status_name(),
            "sample_type": self.sample_type.value,
            "acquisition": {
                "source": self.acquisition_source.value,
                "date": self.acquisition_date.isoformat() if self.acquisition_date else None,
                "donor_institute": self.donor_institute,
                "donor_accession": self.donor_accession,
            },
            "collection_site": self.collection_site.to_dict() if self.collection_site else None,
            "pedigree": self.pedigree,
            "remarks": self.remarks,
            "storage_location": self.storage_location,
            "mls_status": self.mlsstat,
        }

    def _get_status_name(self) -> str:
        names = {
            "100": "Wild",
            "200": "Weedy",
            "300": "Traditional cultivar/Landrace",
            "400": "Breeding/Research material",
            "500": "Advanced/Improved cultivar",
            "600": "GMO",
            "999": "Other",
        }
        return names.get(self.biological_status.value, "Unknown")

    def to_mcpd(self) -> Dict[str, Any]:
        """Export as MCPD format"""
        mcpd = {
            "ACCENUMB": self.accession_id,
            "ACCENAME": self.accession_name,
            "GENUS": self.genus,
            "SPECIES": self.species,
            "SPAUTHOR": self.species_authority,
            "SUBTAXA": self.subtaxa,
            "SAMPSTAT": self.biological_status.value,
            "COLLSRC": self.acquisition_source.value,
            "ACQDATE": self.acquisition_date.strftime("%Y%m%d") if self.acquisition_date else "",
            "DONORCODE": self.donor_institute,
            "DONORNUMB": self.donor_accession,
            "ANCEST": self.pedigree,
            "REMARKS": self.remarks,
            "MLSSTAT": self.mlsstat,
        }

        if self.collection_site:
            mcpd.update({
                "ORIGCTY": self.collection_site.country,
                "COLLSITE": self.collection_site.locality,
                "LATITUDE": self.collection_site.latitude,
                "LONGITUDE": self.collection_site.longitude,
                "ELEVATION": self.collection_site.elevation,
                "COLLDATE": self.collection_site.collection_date.strftime("%Y%m%d") if self.collection_site.collection_date else "",
                "COLLNUMB": "",
                "COLLCODE": self.collection_site.collector_institute,
            })

        return mcpd


class GermplasmPassportService:
    """
    Germplasm passport management
    """

    def __init__(self):
        self.passports: Dict[str, GermplasmPassport] = {}

    def register_accession(
        self,
        accession_id: str,
        accession_name: str,
        genus: str,
        species: str,
        species_authority: str = "",
        subtaxa: str = "",
        common_name: str = "",
        biological_status: str = "999",
        sample_type: str = "seed",
        acquisition_source: str = "99",
        acquisition_date: Optional[str] = None,
        donor_institute: str = "",
        donor_accession: str = "",
        pedigree: str = "",
        remarks: str = "",
        storage_location: str = "",
        mls_status: str = ""
    ) -> GermplasmPassport:
        """Register a new germplasm accession"""
        passport = GermplasmPassport(
            accession_id=accession_id,
            accession_name=accession_name,
            genus=genus,
            species=species,
            species_authority=species_authority,
            subtaxa=subtaxa,
            common_name=common_name,
            biological_status=BiologicalStatus(biological_status),
            sample_type=SampleType(sample_type),
            acquisition_source=AcquisitionSource(acquisition_source),
            acquisition_date=date.fromisoformat(acquisition_date) if acquisition_date else None,
            donor_institute=donor_institute,
            donor_accession=donor_accession,
            pedigree=pedigree,
            remarks=remarks,
            storage_location=storage_location,
            mlsstat=mls_status,
        )

        self.passports[accession_id] = passport
        return passport

    def add_collection_site(
        self,
        accession_id: str,
        country: str,
        state_province: str,
        municipality: str,
        locality: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        elevation: Optional[float] = None,
        collection_date: Optional[str] = None,
        collector_name: str = "",
        collector_institute: str = ""
    ) -> GermplasmPassport:
        """Add collection site information to an accession"""
        if accession_id not in self.passports:
            raise ValueError(f"Accession {accession_id} not found")

        site = CollectionSite(
            country=country,
            state_province=state_province,
            municipality=municipality,
            locality=locality,
            latitude=latitude,
            longitude=longitude,
            elevation=elevation,
            collection_date=date.fromisoformat(collection_date) if collection_date else None,
            collector_name=collector_name,
            collector_institute=collector_institute,
        )

        self.passports[accession_id].collection_site = site
        return self.passports[accession_id]

    def get_passport(self, accession_id: str) -> Optional[Dict[str, Any]]:
        """Get passport data for an accession"""
        if accession_id not in self.passports:
            return None
        return self.passports[accession_id].to_dict()

    def list_passports(
        self,
        genus: Optional[str] = None,
        species: Optional[str] = None,
        biological_status: Optional[str] = None,
        country: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List passports with optional filters"""
        result = []
        for passport in self.passports.values():
            if genus and passport.genus.lower() != genus.lower():
                continue
            if species and passport.species.lower() != species.lower():
                continue
            if biological_status and passport.biological_status.value != biological_status:
                continue
            if country and passport.collection_site:
                if passport.collection_site.country != country:
                    continue
            result.append(passport.to_dict())
        return result

    def export_mcpd(
        self,
        accession_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Export passports in MCPD format"""
        if accession_ids:
            passports = [self.passports[aid] for aid in accession_ids if aid in self.passports]
        else:
            passports = list(self.passports.values())

        return [p.to_mcpd() for p in passports]

    def search(
        self,
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search passports by name, ID, or taxonomy"""
        query_lower = query.lower()
        results = []

        for passport in self.passports.values():
            score = 0

            if query_lower in passport.accession_id.lower():
                score += 10
            if query_lower in passport.accession_name.lower():
                score += 8
            if query_lower in passport.genus.lower():
                score += 5
            if query_lower in passport.species.lower():
                score += 5
            if query_lower in passport.common_name.lower():
                score += 3

            if score > 0:
                results.append((score, passport.to_dict()))

        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:limit]]

    def get_statistics(self) -> Dict[str, Any]:
        """Get collection statistics"""
        total = len(self.passports)

        by_genus = {}
        by_status = {}
        by_country = {}

        for passport in self.passports.values():
            # By genus
            genus = passport.genus
            by_genus[genus] = by_genus.get(genus, 0) + 1

            # By biological status
            status = passport._get_status_name()
            by_status[status] = by_status.get(status, 0) + 1

            # By country
            if passport.collection_site:
                country = passport.collection_site.country
                by_country[country] = by_country.get(country, 0) + 1

        return {
            "total_accessions": total,
            "by_genus": by_genus,
            "by_biological_status": by_status,
            "by_country": by_country,
            "with_coordinates": sum(1 for p in self.passports.values()
                                   if p.collection_site and p.collection_site.latitude),
        }


# Singleton
_passport_service: Optional[GermplasmPassportService] = None


def get_passport_service() -> GermplasmPassportService:
    """Get or create passport service singleton"""
    global _passport_service
    if _passport_service is None:
        _passport_service = GermplasmPassportService()
    return _passport_service
