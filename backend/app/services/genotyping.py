"""
BrAPI Genotyping Service
Manages variant sets, calls, call sets, references, and marker positions
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import random
import string


class GenotypingService:
    """Service for BrAPI genotyping operations"""
    
    def __init__(self):
        self._variant_sets: Dict[str, Dict] = {}
        self._call_sets: Dict[str, Dict] = {}
        self._calls: List[Dict] = []
        self._references: Dict[str, Dict] = {}
        self._reference_sets: Dict[str, Dict] = {}
        self._marker_positions: List[Dict] = []
        self._vendor_orders: Dict[str, Dict] = {}
        self._init_demo_data()
    
    def _init_demo_data(self):
        """Initialize demo data"""
        # Reference sets (genomes)
        self._reference_sets = {
            "refset001": {
                "referenceSetDbId": "refset001",
                "referenceSetName": "IRGSP-1.0",
                "description": "International Rice Genome Sequencing Project Reference",
                "assemblyPUI": "GCF_001433935.1",
                "sourceURI": "https://www.ncbi.nlm.nih.gov/assembly/GCF_001433935.1",
                "species": {"genus": "Oryza", "species": "sativa"},
                "isDerived": False,
            },
            "refset002": {
                "referenceSetDbId": "refset002",
                "referenceSetName": "IWGSC RefSeq v2.1",
                "description": "International Wheat Genome Sequencing Consortium",
                "assemblyPUI": "GCF_018294505.1",
                "sourceURI": "https://www.ncbi.nlm.nih.gov/assembly/GCF_018294505.1",
                "species": {"genus": "Triticum", "species": "aestivum"},
                "isDerived": False,
            },
            "refset003": {
                "referenceSetDbId": "refset003",
                "referenceSetName": "B73 RefGen_v5",
                "description": "Maize B73 Reference Genome v5",
                "assemblyPUI": "GCF_902167145.1",
                "sourceURI": "https://www.ncbi.nlm.nih.gov/assembly/GCF_902167145.1",
                "species": {"genus": "Zea", "species": "mays"},
                "isDerived": False,
            },
        }
        
        # References (chromosomes)
        chromosomes_rice = [f"Chr{i}" for i in range(1, 13)]
        chromosomes_wheat = [f"{i}{arm}" for i in range(1, 8) for arm in ["A", "B", "D"]]
        chromosomes_maize = [f"Chr{i}" for i in range(1, 11)]
        
        for i, chrom in enumerate(chromosomes_rice):
            self._references[f"ref_rice_{i+1}"] = {
                "referenceDbId": f"ref_rice_{i+1}",
                "referenceName": chrom,
                "referenceSetDbId": "refset001",
                "length": random.randint(20000000, 45000000),
                "md5checksum": ''.join(random.choices(string.hexdigits.lower(), k=32)),
                "sourceURI": f"https://rice.plantbiology.msu.edu/{chrom}",
                "isDerived": False,
            }
        
        for i, chrom in enumerate(chromosomes_wheat[:10]):  # First 10 for demo
            self._references[f"ref_wheat_{i+1}"] = {
                "referenceDbId": f"ref_wheat_{i+1}",
                "referenceName": chrom,
                "referenceSetDbId": "refset002",
                "length": random.randint(500000000, 800000000),
                "md5checksum": ''.join(random.choices(string.hexdigits.lower(), k=32)),
                "isDerived": False,
            }
        
        for i, chrom in enumerate(chromosomes_maize):
            self._references[f"ref_maize_{i+1}"] = {
                "referenceDbId": f"ref_maize_{i+1}",
                "referenceName": chrom,
                "referenceSetDbId": "refset003",
                "length": random.randint(150000000, 310000000),
                "md5checksum": ''.join(random.choices(string.hexdigits.lower(), k=32)),
                "isDerived": False,
            }
        
        # Variant sets
        self._variant_sets = {
            "vs001": {
                "variantSetDbId": "vs001",
                "variantSetName": "Rice_GBS_2024",
                "studyDbId": "study001",
                "studyName": "Rice Diversity Panel",
                "referenceSetDbId": "refset001",
                "variantCount": 45000,
                "callSetCount": 384,
                "analysis": [{"analysisDbId": "an001", "analysisName": "GATK HaplotypeCaller", "software": "GATK 4.2", "type": "SNP calling"}],
                "availableFormats": [{"dataFormat": "VCF", "fileURL": "/data/rice_gbs_2024.vcf.gz"}],
                "created": "2024-01-15",
            },
            "vs002": {
                "variantSetDbId": "vs002",
                "variantSetName": "Wheat_SNP_Array",
                "studyDbId": "study002",
                "studyName": "Wheat Breeding Lines",
                "referenceSetDbId": "refset002",
                "variantCount": 90000,
                "callSetCount": 192,
                "analysis": [{"analysisDbId": "an002", "analysisName": "Axiom Analysis", "software": "Axiom Suite 2.0", "type": "Array genotyping"}],
                "availableFormats": [{"dataFormat": "VCF", "fileURL": "/data/wheat_snp_array.vcf.gz"}],
                "created": "2024-02-01",
            },
            "vs003": {
                "variantSetDbId": "vs003",
                "variantSetName": "Maize_WGS_Pilot",
                "studyDbId": "study003",
                "studyName": "Maize Inbred Lines",
                "referenceSetDbId": "refset003",
                "variantCount": 125000,
                "callSetCount": 48,
                "analysis": [{"analysisDbId": "an003", "analysisName": "DeepVariant", "software": "DeepVariant 1.4", "type": "WGS variant calling"}],
                "availableFormats": [{"dataFormat": "VCF", "fileURL": "/data/maize_wgs.vcf.gz"}],
                "created": "2024-02-20",
            },
        }
        
        # Call sets (samples)
        sample_names_rice = [f"IRIS_{i:03d}" for i in range(1, 385)]
        sample_names_wheat = [f"CIMMYT_W{i:03d}" for i in range(1, 193)]
        sample_names_maize = [f"B73xMo17_F2_{i:02d}" for i in range(1, 49)]
        
        for i, name in enumerate(sample_names_rice[:50]):  # First 50 for demo
            self._call_sets[f"cs_rice_{i+1}"] = {
                "callSetDbId": f"cs_rice_{i+1}",
                "callSetName": name,
                "sampleDbId": f"sample_rice_{i+1}",
                "variantSetDbIds": ["vs001"],
                "studyDbId": "study001",
                "created": "2024-01-15",
            }
        
        for i, name in enumerate(sample_names_wheat[:30]):
            self._call_sets[f"cs_wheat_{i+1}"] = {
                "callSetDbId": f"cs_wheat_{i+1}",
                "callSetName": name,
                "sampleDbId": f"sample_wheat_{i+1}",
                "variantSetDbIds": ["vs002"],
                "studyDbId": "study002",
                "created": "2024-02-01",
            }
        
        for i, name in enumerate(sample_names_maize):
            self._call_sets[f"cs_maize_{i+1}"] = {
                "callSetDbId": f"cs_maize_{i+1}",
                "callSetName": name,
                "sampleDbId": f"sample_maize_{i+1}",
                "variantSetDbIds": ["vs003"],
                "studyDbId": "study003",
                "created": "2024-02-20",
            }
        
        # Generate calls for demo
        self._generate_demo_calls()
        
        # Marker positions
        self._generate_marker_positions()
        
        # Vendor orders
        self._vendor_orders = {
            "vo001": {
                "vendorOrderDbId": "vo001",
                "clientId": "client001",
                "numberOfSamples": 96,
                "orderId": "ORD-2024-001",
                "requiredServiceInfo": {"serviceId": "GBS", "serviceName": "Genotyping-by-Sequencing"},
                "serviceIds": ["GBS"],
                "status": "completed",
                "submissionDate": "2024-01-10",
                "resultDate": "2024-02-15",
            },
            "vo002": {
                "vendorOrderDbId": "vo002",
                "clientId": "client001",
                "numberOfSamples": 384,
                "orderId": "ORD-2024-002",
                "requiredServiceInfo": {"serviceId": "SNP_ARRAY", "serviceName": "SNP Array Genotyping"},
                "serviceIds": ["SNP_ARRAY"],
                "status": "in_progress",
                "submissionDate": "2024-03-01",
            },
            "vo003": {
                "vendorOrderDbId": "vo003",
                "clientId": "client002",
                "numberOfSamples": 48,
                "orderId": "ORD-2024-003",
                "requiredServiceInfo": {"serviceId": "WGS", "serviceName": "Whole Genome Sequencing"},
                "serviceIds": ["WGS"],
                "status": "submitted",
                "submissionDate": "2024-03-10",
            },
        }

    
    def _generate_demo_calls(self):
        """Generate demo genotype calls"""
        genotypes = ["0/0", "0/1", "1/1", "./.", "0/2", "1/2"]
        weights = [0.4, 0.35, 0.2, 0.03, 0.01, 0.01]
        
        # Generate calls for rice variant set
        rice_call_sets = [cs for cs_id, cs in self._call_sets.items() if "rice" in cs_id][:20]
        for i in range(100):  # 100 variants
            variant_id = f"var_rice_{i+1}"
            variant_name = f"SNP_Chr{(i % 12) + 1}_{random.randint(10000, 9999999)}"
            for cs in rice_call_sets:
                gt = random.choices(genotypes, weights=weights)[0]
                self._calls.append({
                    "callSetDbId": cs["callSetDbId"],
                    "callSetName": cs["callSetName"],
                    "variantDbId": variant_id,
                    "variantName": variant_name,
                    "variantSetDbId": "vs001",
                    "genotype": {"values": gt.split("/")},
                    "genotypeValue": gt,
                    "genotypeQuality": random.randint(20, 99) if gt != "./." else 0,
                    "readDepth": random.randint(10, 100) if gt != "./." else 0,
                    "genotypeMetadata": [{"dataType": "integer", "fieldName": "DP", "fieldValue": str(random.randint(10, 100))}],
                })
    
    def _generate_marker_positions(self):
        """Generate marker positions for linkage maps"""
        # Rice linkage map
        for chrom in range(1, 13):
            num_markers = random.randint(50, 150)
            positions = sorted(random.sample(range(0, 200), num_markers))
            for i, pos in enumerate(positions):
                self._marker_positions.append({
                    "markerPositionDbId": f"mp_rice_{chrom}_{i+1}",
                    "markerDbId": f"marker_rice_{chrom}_{i+1}",
                    "markerName": f"RM{chrom}{i+1:03d}",
                    "mapDbId": "map_rice_001",
                    "mapName": "Rice Linkage Map v1",
                    "linkageGroupName": f"Chr{chrom}",
                    "position": pos,
                    "positionUnit": "cM",
                })
    
    # Variant Sets
    def list_variant_sets(
        self,
        variant_set_db_id: Optional[str] = None,
        study_db_id: Optional[str] = None,
        reference_set_db_id: Optional[str] = None,
        page: int = 0,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List variant sets with optional filters"""
        results = list(self._variant_sets.values())
        
        if variant_set_db_id:
            results = [vs for vs in results if vs["variantSetDbId"] == variant_set_db_id]
        if study_db_id:
            results = [vs for vs in results if vs.get("studyDbId") == study_db_id]
        if reference_set_db_id:
            results = [vs for vs in results if vs.get("referenceSetDbId") == reference_set_db_id]
        
        total = len(results)
        start = page * page_size
        end = start + page_size
        
        return {
            "data": results[start:end],
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalCount": total,
                "totalPages": (total + page_size - 1) // page_size,
            },
        }
    
    def get_variant_set(self, variant_set_db_id: str) -> Optional[Dict]:
        """Get a single variant set by ID"""
        return self._variant_sets.get(variant_set_db_id)
    
    def create_variant_set(self, data: Dict) -> Dict:
        """Create a new variant set"""
        vs_id = f"vs{len(self._variant_sets) + 1:03d}"
        variant_set = {
            "variantSetDbId": vs_id,
            "variantSetName": data.get("variantSetName", f"VariantSet_{vs_id}"),
            "studyDbId": data.get("studyDbId"),
            "studyName": data.get("studyName"),
            "referenceSetDbId": data.get("referenceSetDbId"),
            "variantCount": data.get("variantCount", 0),
            "callSetCount": data.get("callSetCount", 0),
            "analysis": data.get("analysis", []),
            "availableFormats": data.get("availableFormats", []),
            "created": datetime.now().strftime("%Y-%m-%d"),
        }
        self._variant_sets[vs_id] = variant_set
        return variant_set
    
    # Call Sets
    def list_call_sets(
        self,
        call_set_db_id: Optional[str] = None,
        call_set_name: Optional[str] = None,
        variant_set_db_id: Optional[str] = None,
        sample_db_id: Optional[str] = None,
        page: int = 0,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List call sets with optional filters"""
        results = list(self._call_sets.values())
        
        if call_set_db_id:
            results = [cs for cs in results if cs["callSetDbId"] == call_set_db_id]
        if call_set_name:
            results = [cs for cs in results if call_set_name.lower() in cs["callSetName"].lower()]
        if variant_set_db_id:
            results = [cs for cs in results if variant_set_db_id in cs.get("variantSetDbIds", [])]
        if sample_db_id:
            results = [cs for cs in results if cs.get("sampleDbId") == sample_db_id]
        
        total = len(results)
        start = page * page_size
        end = start + page_size
        
        return {
            "data": results[start:end],
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalCount": total,
                "totalPages": (total + page_size - 1) // page_size,
            },
        }
    
    def get_call_set(self, call_set_db_id: str) -> Optional[Dict]:
        """Get a single call set by ID"""
        return self._call_sets.get(call_set_db_id)
    
    # Calls
    def list_calls(
        self,
        call_set_db_id: Optional[str] = None,
        variant_db_id: Optional[str] = None,
        variant_set_db_id: Optional[str] = None,
        page: int = 0,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """List genotype calls with optional filters"""
        results = self._calls.copy()
        
        if call_set_db_id:
            results = [c for c in results if c["callSetDbId"] == call_set_db_id]
        if variant_db_id:
            results = [c for c in results if c["variantDbId"] == variant_db_id]
        if variant_set_db_id:
            results = [c for c in results if c.get("variantSetDbId") == variant_set_db_id]
        
        total = len(results)
        start = page * page_size
        end = start + page_size
        
        return {
            "data": results[start:end],
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalCount": total,
                "totalPages": (total + page_size - 1) // page_size,
            },
        }
    
    def get_calls_statistics(self, variant_set_db_id: Optional[str] = None) -> Dict:
        """Get statistics for genotype calls"""
        calls = self._calls
        if variant_set_db_id:
            calls = [c for c in calls if c.get("variantSetDbId") == variant_set_db_id]
        
        total = len(calls)
        if total == 0:
            return {"total": 0, "heterozygous": 0, "homozygousRef": 0, "homozygousAlt": 0, "missing": 0, "avgQuality": 0}
        
        het = sum(1 for c in calls if c["genotypeValue"] == "0/1")
        hom_ref = sum(1 for c in calls if c["genotypeValue"] == "0/0")
        hom_alt = sum(1 for c in calls if c["genotypeValue"] == "1/1")
        missing = sum(1 for c in calls if c["genotypeValue"] == "./.")
        avg_qual = sum(c["genotypeQuality"] for c in calls) / total
        
        return {
            "total": total,
            "heterozygous": het,
            "homozygousRef": hom_ref,
            "homozygousAlt": hom_alt,
            "missing": missing,
            "avgQuality": round(avg_qual, 1),
            "heterozygosityRate": round(het / total * 100, 2) if total > 0 else 0,
            "missingRate": round(missing / total * 100, 2) if total > 0 else 0,
        }
    
    # References
    def list_references(
        self,
        reference_db_id: Optional[str] = None,
        reference_set_db_id: Optional[str] = None,
        page: int = 0,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List references (chromosomes)"""
        results = list(self._references.values())
        
        if reference_db_id:
            results = [r for r in results if r["referenceDbId"] == reference_db_id]
        if reference_set_db_id:
            results = [r for r in results if r.get("referenceSetDbId") == reference_set_db_id]
        
        total = len(results)
        start = page * page_size
        end = start + page_size
        
        return {
            "data": results[start:end],
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalCount": total,
                "totalPages": (total + page_size - 1) // page_size,
            },
        }
    
    def get_reference(self, reference_db_id: str) -> Optional[Dict]:
        """Get a single reference by ID"""
        return self._references.get(reference_db_id)
    
    # Reference Sets
    def list_reference_sets(
        self,
        reference_set_db_id: Optional[str] = None,
        page: int = 0,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List reference sets (genomes)"""
        results = list(self._reference_sets.values())
        
        if reference_set_db_id:
            results = [rs for rs in results if rs["referenceSetDbId"] == reference_set_db_id]
        
        total = len(results)
        start = page * page_size
        end = start + page_size
        
        return {
            "data": results[start:end],
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalCount": total,
                "totalPages": (total + page_size - 1) // page_size,
            },
        }
    
    # Marker Positions
    def list_marker_positions(
        self,
        map_db_id: Optional[str] = None,
        linkage_group_name: Optional[str] = None,
        min_position: Optional[float] = None,
        max_position: Optional[float] = None,
        page: int = 0,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """List marker positions on linkage maps"""
        results = self._marker_positions.copy()
        
        if map_db_id:
            results = [mp for mp in results if mp.get("mapDbId") == map_db_id]
        if linkage_group_name:
            results = [mp for mp in results if mp.get("linkageGroupName") == linkage_group_name]
        if min_position is not None:
            results = [mp for mp in results if mp["position"] >= min_position]
        if max_position is not None:
            results = [mp for mp in results if mp["position"] <= max_position]
        
        total = len(results)
        start = page * page_size
        end = start + page_size
        
        return {
            "data": results[start:end],
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalCount": total,
                "totalPages": (total + page_size - 1) // page_size,
            },
        }
    
    # Vendor Orders
    def list_vendor_orders(
        self,
        vendor_order_db_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 0,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List vendor orders"""
        results = list(self._vendor_orders.values())
        
        if vendor_order_db_id:
            results = [vo for vo in results if vo["vendorOrderDbId"] == vendor_order_db_id]
        if status:
            results = [vo for vo in results if vo.get("status") == status]
        
        total = len(results)
        start = page * page_size
        end = start + page_size
        
        return {
            "data": results[start:end],
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalCount": total,
                "totalPages": (total + page_size - 1) // page_size,
            },
        }
    
    def get_vendor_order(self, vendor_order_db_id: str) -> Optional[Dict]:
        """Get a single vendor order by ID"""
        return self._vendor_orders.get(vendor_order_db_id)
    
    def create_vendor_order(self, data: Dict) -> Dict:
        """Create a new vendor order"""
        vo_id = f"vo{len(self._vendor_orders) + 1:03d}"
        order = {
            "vendorOrderDbId": vo_id,
            "clientId": data.get("clientId", "client001"),
            "numberOfSamples": data.get("numberOfSamples", 0),
            "orderId": f"ORD-{datetime.now().year}-{len(self._vendor_orders) + 1:03d}",
            "requiredServiceInfo": data.get("requiredServiceInfo", {}),
            "serviceIds": data.get("serviceIds", []),
            "status": "submitted",
            "submissionDate": datetime.now().strftime("%Y-%m-%d"),
        }
        self._vendor_orders[vo_id] = order
        return order
    
    def update_vendor_order_status(self, vendor_order_db_id: str, status: str) -> Optional[Dict]:
        """Update vendor order status"""
        if vendor_order_db_id in self._vendor_orders:
            self._vendor_orders[vendor_order_db_id]["status"] = status
            if status == "completed":
                self._vendor_orders[vendor_order_db_id]["resultDate"] = datetime.now().strftime("%Y-%m-%d")
            return self._vendor_orders[vendor_order_db_id]
        return None


# Singleton instance
genotyping_service = GenotypingService()
