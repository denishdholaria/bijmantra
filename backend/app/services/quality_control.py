"""
Quality Control Service for Plant Breeding
Seed quality testing, sample analysis, and certification

Features:
- Seed purity testing
- Moisture content analysis
- Seed health testing
- Genetic purity (grow-out tests)
- Quality certification
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TestType(str, Enum):
    PURITY = "purity"
    MOISTURE = "moisture"
    GERMINATION = "germination"
    VIGOR = "vigor"
    HEALTH = "health"
    GENETIC_PURITY = "genetic_purity"


class QualityGrade(str, Enum):
    FOUNDATION = "foundation"
    CERTIFIED = "certified"
    TRUTHFUL = "truthful"
    RESEARCH = "research"


@dataclass
class QualityTest:
    """Quality test record"""
    test_id: str
    sample_id: str
    test_type: TestType
    test_date: date
    result_value: float
    result_unit: str
    standard_min: float
    standard_max: float
    passed: bool
    tester: str
    method: str
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "sample_id": self.sample_id,
            "test_type": self.test_type.value,
            "test_date": self.test_date.isoformat(),
            "result_value": round(self.result_value, 2),
            "result_unit": self.result_unit,
            "standard_range": [self.standard_min, self.standard_max],
            "passed": self.passed,
            "tester": self.tester,
            "method": self.method,
            "notes": self.notes,
        }


@dataclass
class QualitySample:
    """Quality control sample"""
    sample_id: str
    lot_id: str
    variety: str
    sample_date: date
    sample_weight: float
    source: str
    tests: List[str] = None  # test_ids
    overall_status: str = "pending"  # pending, passed, failed
    certificate_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "lot_id": self.lot_id,
            "variety": self.variety,
            "sample_date": self.sample_date.isoformat(),
            "sample_weight_g": self.sample_weight,
            "source": self.source,
            "test_count": len(self.tests) if self.tests else 0,
            "overall_status": self.overall_status,
            "certificate_id": self.certificate_id,
        }


# Quality standards by seed class
QUALITY_STANDARDS = {
    "foundation": {
        "purity": {"min": 99.0, "max": 100.0, "unit": "%"},
        "germination": {"min": 90.0, "max": 100.0, "unit": "%"},
        "moisture": {"min": 0.0, "max": 12.0, "unit": "%"},
        "genetic_purity": {"min": 99.5, "max": 100.0, "unit": "%"},
    },
    "certified": {
        "purity": {"min": 98.0, "max": 100.0, "unit": "%"},
        "germination": {"min": 85.0, "max": 100.0, "unit": "%"},
        "moisture": {"min": 0.0, "max": 13.0, "unit": "%"},
        "genetic_purity": {"min": 98.0, "max": 100.0, "unit": "%"},
    },
    "truthful": {
        "purity": {"min": 95.0, "max": 100.0, "unit": "%"},
        "germination": {"min": 80.0, "max": 100.0, "unit": "%"},
        "moisture": {"min": 0.0, "max": 14.0, "unit": "%"},
    },
}


class QualityControlService:
    """
    Quality control for seed certification
    """
    
    def __init__(self):
        self.samples: Dict[str, QualitySample] = {}
        self.tests: Dict[str, QualityTest] = {}
        self._sample_counter = 0
        self._test_counter = 0
        self._cert_counter = 0
    
    def register_sample(
        self,
        lot_id: str,
        variety: str,
        sample_date: str,
        sample_weight: float,
        source: str
    ) -> QualitySample:
        """Register a sample for quality testing"""
        self._sample_counter += 1
        sample_id = f"QC-{self._sample_counter:06d}"
        
        sample = QualitySample(
            sample_id=sample_id,
            lot_id=lot_id,
            variety=variety,
            sample_date=date.fromisoformat(sample_date),
            sample_weight=sample_weight,
            source=source,
            tests=[],
        )
        
        self.samples[sample_id] = sample
        return sample
    
    def record_test(
        self,
        sample_id: str,
        test_type: str,
        result_value: float,
        tester: str,
        method: str,
        seed_class: str = "certified",
        notes: str = ""
    ) -> QualityTest:
        """
        Record a quality test result
        
        Automatically checks against standards for the seed class.
        """
        if sample_id not in self.samples:
            raise ValueError(f"Sample {sample_id} not found")
        
        test_type_enum = TestType(test_type)
        
        # Get standards
        standards = QUALITY_STANDARDS.get(seed_class, QUALITY_STANDARDS["certified"])
        test_standards = standards.get(test_type, {"min": 0, "max": 100, "unit": "%"})
        
        # Check if passed
        passed = test_standards["min"] <= result_value <= test_standards["max"]
        
        self._test_counter += 1
        test_id = f"TEST-{self._test_counter:06d}"
        
        test = QualityTest(
            test_id=test_id,
            sample_id=sample_id,
            test_type=test_type_enum,
            test_date=date.today(),
            result_value=result_value,
            result_unit=test_standards["unit"],
            standard_min=test_standards["min"],
            standard_max=test_standards["max"],
            passed=passed,
            tester=tester,
            method=method,
            notes=notes,
        )
        
        self.tests[test_id] = test
        self.samples[sample_id].tests.append(test_id)
        
        # Update sample status
        self._update_sample_status(sample_id)
        
        return test
    
    def _update_sample_status(self, sample_id: str):
        """Update overall sample status based on tests"""
        sample = self.samples[sample_id]
        
        if not sample.tests:
            sample.overall_status = "pending"
            return
        
        all_passed = all(
            self.tests[tid].passed for tid in sample.tests
        )
        
        sample.overall_status = "passed" if all_passed else "failed"
    
    def issue_certificate(
        self,
        sample_id: str,
        seed_class: str,
        valid_months: int = 12
    ) -> Dict[str, Any]:
        """
        Issue quality certificate for a sample
        
        Only issues if all required tests passed.
        """
        if sample_id not in self.samples:
            raise ValueError(f"Sample {sample_id} not found")
        
        sample = self.samples[sample_id]
        
        if sample.overall_status != "passed":
            raise ValueError(f"Sample has not passed all tests")
        
        # Check required tests for seed class
        required_tests = list(QUALITY_STANDARDS.get(seed_class, {}).keys())
        completed_tests = [self.tests[tid].test_type.value for tid in sample.tests]
        
        missing = set(required_tests) - set(completed_tests)
        if missing:
            raise ValueError(f"Missing required tests: {missing}")
        
        self._cert_counter += 1
        cert_id = f"CERT-{self._cert_counter:06d}"
        
        sample.certificate_id = cert_id
        
        return {
            "certificate_id": cert_id,
            "sample_id": sample_id,
            "lot_id": sample.lot_id,
            "variety": sample.variety,
            "seed_class": seed_class,
            "issue_date": date.today().isoformat(),
            "valid_until": (date.today().replace(year=date.today().year + 1)).isoformat(),
            "tests_passed": len(sample.tests),
            "status": "issued",
        }
    
    def get_sample(self, sample_id: str) -> Optional[Dict[str, Any]]:
        """Get sample details with test results"""
        if sample_id not in self.samples:
            return None
        
        sample = self.samples[sample_id]
        test_results = [self.tests[tid].to_dict() for tid in sample.tests]
        
        return {
            **sample.to_dict(),
            "tests": test_results,
        }
    
    def list_samples(
        self,
        status: Optional[str] = None,
        lot_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List samples with optional filters"""
        result = []
        for sample in self.samples.values():
            if status and sample.overall_status != status:
                continue
            if lot_id and sample.lot_id != lot_id:
                continue
            result.append(sample.to_dict())
        return result
    
    def get_standards(self, seed_class: str = "certified") -> Dict[str, Any]:
        """Get quality standards for a seed class"""
        return {
            "seed_class": seed_class,
            "standards": QUALITY_STANDARDS.get(seed_class, QUALITY_STANDARDS["certified"]),
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get QC summary statistics"""
        total_samples = len(self.samples)
        by_status = {}
        for sample in self.samples.values():
            status = sample.overall_status
            by_status[status] = by_status.get(status, 0) + 1
        
        total_tests = len(self.tests)
        passed_tests = sum(1 for t in self.tests.values() if t.passed)
        
        return {
            "total_samples": total_samples,
            "samples_by_status": by_status,
            "total_tests": total_tests,
            "tests_passed": passed_tests,
            "tests_failed": total_tests - passed_tests,
            "pass_rate_percent": round(passed_tests / total_tests * 100, 1) if total_tests > 0 else 0,
            "certificates_issued": sum(1 for s in self.samples.values() if s.certificate_id),
        }


# Singleton
_qc_service: Optional[QualityControlService] = None


def get_qc_service() -> QualityControlService:
    """Get or create QC service singleton"""
    global _qc_service
    if _qc_service is None:
        _qc_service = QualityControlService()
    return _qc_service
