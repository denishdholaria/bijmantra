"""
Material Transfer Agreement (MTA) Service

Manages MTAs for germplasm exchange under ITPGRFA (International Treaty on 
Plant Genetic Resources for Food and Agriculture) and institutional agreements.

MTA Types:
- SMTA: Standard Material Transfer Agreement (ITPGRFA Annex I crops)
- Institutional MTA: Bilateral agreements between institutions
- Research MTA: For research-only use
- Commercial MTA: For commercial development (requires benefit sharing)
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
import enum


class MTAType(str, enum.Enum):
    SMTA = "smta"  # Standard MTA under ITPGRFA
    INSTITUTIONAL = "institutional"  # Bilateral institutional agreement
    RESEARCH = "research"  # Research-only use
    COMMERCIAL = "commercial"  # Commercial development


class MTAStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PENDING_SIGNATURE = "pending_signature"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    REJECTED = "rejected"


class BenefitSharingType(str, enum.Enum):
    NONE = "none"  # SMTA - no direct benefit sharing
    MONETARY = "monetary"  # Royalty payments
    NON_MONETARY = "non_monetary"  # Technology transfer, training
    BOTH = "both"


# MTA Templates
MTA_TEMPLATES = {
    "smta": {
        "id": "smta-v1",
        "name": "Standard Material Transfer Agreement (SMTA)",
        "type": MTAType.SMTA,
        "description": "Standard MTA under the International Treaty on Plant Genetic Resources for Food and Agriculture (ITPGRFA) for Annex I crops",
        "version": "1.0",
        "clauses": [
            {"id": "1", "title": "Definitions", "required": True},
            {"id": "2", "title": "Rights and Obligations of Provider", "required": True},
            {"id": "3", "title": "Rights and Obligations of Recipient", "required": True},
            {"id": "4", "title": "Benefit Sharing", "required": True},
            {"id": "5", "title": "Dispute Settlement", "required": True},
        ],
        "benefit_sharing": BenefitSharingType.NONE,
        "duration_years": None,  # Perpetual
        "requires_approval": False,  # Auto-approved for SMTA
    },
    "institutional": {
        "id": "inst-v1",
        "name": "Institutional Material Transfer Agreement",
        "type": MTAType.INSTITUTIONAL,
        "description": "Bilateral agreement between research institutions for germplasm exchange",
        "version": "1.0",
        "clauses": [
            {"id": "1", "title": "Definitions", "required": True},
            {"id": "2", "title": "Material Description", "required": True},
            {"id": "3", "title": "Permitted Uses", "required": True},
            {"id": "4", "title": "Restrictions", "required": True},
            {"id": "5", "title": "Intellectual Property", "required": True},
            {"id": "6", "title": "Publication Rights", "required": True},
            {"id": "7", "title": "Liability", "required": True},
            {"id": "8", "title": "Term and Termination", "required": True},
        ],
        "benefit_sharing": BenefitSharingType.NON_MONETARY,
        "duration_years": 5,
        "requires_approval": True,
    },
    "research": {
        "id": "research-v1",
        "name": "Research Material Transfer Agreement",
        "type": MTAType.RESEARCH,
        "description": "Agreement for research-only use of germplasm, no commercial development",
        "version": "1.0",
        "clauses": [
            {"id": "1", "title": "Definitions", "required": True},
            {"id": "2", "title": "Material Description", "required": True},
            {"id": "3", "title": "Research Use Only", "required": True},
            {"id": "4", "title": "No Commercial Use", "required": True},
            {"id": "5", "title": "Publication Acknowledgment", "required": True},
            {"id": "6", "title": "Return/Destruction of Material", "required": False},
        ],
        "benefit_sharing": BenefitSharingType.NONE,
        "duration_years": 3,
        "requires_approval": True,
    },
    "commercial": {
        "id": "commercial-v1",
        "name": "Commercial Material Transfer Agreement",
        "type": MTAType.COMMERCIAL,
        "description": "Agreement for commercial development with benefit sharing provisions",
        "version": "1.0",
        "clauses": [
            {"id": "1", "title": "Definitions", "required": True},
            {"id": "2", "title": "Material Description", "required": True},
            {"id": "3", "title": "License Grant", "required": True},
            {"id": "4", "title": "Field of Use", "required": True},
            {"id": "5", "title": "Royalty Payments", "required": True},
            {"id": "6", "title": "Milestone Payments", "required": False},
            {"id": "7", "title": "Intellectual Property", "required": True},
            {"id": "8", "title": "Audit Rights", "required": True},
            {"id": "9", "title": "Confidentiality", "required": True},
            {"id": "10", "title": "Term and Termination", "required": True},
        ],
        "benefit_sharing": BenefitSharingType.BOTH,
        "duration_years": 10,
        "requires_approval": True,
    },
}


class MTAService:
    """Service for managing Material Transfer Agreements"""

    def __init__(self):
        self.mtas: dict = {}
        self.mta_counter = 1000
        self._init_demo_data()

    def _init_demo_data(self):
        """Initialize demo MTAs"""
        demo_mtas = [
            {
                "id": str(uuid4()),
                "mta_number": "MTA-2024-001",
                "type": MTAType.SMTA,
                "template_id": "smta-v1",
                "status": MTAStatus.ACTIVE,
                "provider": {
                    "institution": "Bijmantra Seed Bank",
                    "country": "India",
                    "contact": "Dr. Priya Sharma",
                    "email": "priya@example.org",
                },
                "recipient": {
                    "institution": "CIMMYT",
                    "country": "Mexico",
                    "contact": "Dr. Maria Garcia",
                    "email": "m.garcia@cimmyt.org",
                },
                "accessions": ["ACC-2024-001", "ACC-2024-002", "ACC-2024-003"],
                "accession_count": 3,
                "crops": ["Wheat", "Wheat", "Wheat"],
                "purpose": "Drought tolerance research under ITPGRFA",
                "benefit_sharing": {
                    "type": BenefitSharingType.NONE,
                    "details": "Standard SMTA benefit sharing through multilateral system",
                },
                "created_date": "2024-10-15",
                "signed_date": "2024-10-20",
                "effective_date": "2024-10-20",
                "expiry_date": None,
                "exchange_id": "EX-2024-045",
            },
            {
                "id": str(uuid4()),
                "mta_number": "MTA-2024-002",
                "type": MTAType.INSTITUTIONAL,
                "template_id": "inst-v1",
                "status": MTAStatus.ACTIVE,
                "provider": {
                    "institution": "IRRI",
                    "country": "Philippines",
                    "contact": "Dr. Juan Santos",
                    "email": "j.santos@irri.org",
                },
                "recipient": {
                    "institution": "Bijmantra Seed Bank",
                    "country": "India",
                    "contact": "Dr. Raj Patel",
                    "email": "raj@example.org",
                },
                "accessions": ["IRRI-ACC-5001", "IRRI-ACC-5002"],
                "accession_count": 2,
                "crops": ["Rice", "Rice"],
                "purpose": "Collaborative breeding for submergence tolerance",
                "benefit_sharing": {
                    "type": BenefitSharingType.NON_MONETARY,
                    "details": "Joint publication, germplasm sharing, training exchange",
                },
                "created_date": "2024-09-01",
                "signed_date": "2024-09-15",
                "effective_date": "2024-09-15",
                "expiry_date": "2029-09-15",
                "exchange_id": "EX-2024-044",
            },
            {
                "id": str(uuid4()),
                "mta_number": "MTA-2024-003",
                "type": MTAType.RESEARCH,
                "template_id": "research-v1",
                "status": MTAStatus.PENDING_SIGNATURE,
                "provider": {
                    "institution": "Bijmantra Seed Bank",
                    "country": "India",
                    "contact": "Dr. Priya Sharma",
                    "email": "priya@example.org",
                },
                "recipient": {
                    "institution": "University of California Davis",
                    "country": "USA",
                    "contact": "Prof. John Smith",
                    "email": "jsmith@ucdavis.edu",
                },
                "accessions": ["ACC-2024-010", "ACC-2024-011", "ACC-2024-012", "ACC-2024-013", "ACC-2024-014"],
                "accession_count": 5,
                "crops": ["Sorghum", "Sorghum", "Sorghum", "Sorghum", "Sorghum"],
                "purpose": "PhD research on heat stress tolerance mechanisms",
                "benefit_sharing": {
                    "type": BenefitSharingType.NONE,
                    "details": "Research use only, acknowledgment in publications",
                },
                "created_date": "2024-11-01",
                "signed_date": None,
                "effective_date": None,
                "expiry_date": None,
                "exchange_id": "EX-2024-043",
            },
            {
                "id": str(uuid4()),
                "mta_number": "MTA-2024-004",
                "type": MTAType.COMMERCIAL,
                "template_id": "commercial-v1",
                "status": MTAStatus.PENDING_REVIEW,
                "provider": {
                    "institution": "Bijmantra Seed Bank",
                    "country": "India",
                    "contact": "Dr. Priya Sharma",
                    "email": "priya@example.org",
                },
                "recipient": {
                    "institution": "AgriCorp Seeds Ltd",
                    "country": "India",
                    "contact": "Mr. Vikram Mehta",
                    "email": "vmehta@agricorp.com",
                },
                "accessions": ["ACC-2024-020"],
                "accession_count": 1,
                "crops": ["Chickpea"],
                "purpose": "Commercial variety development - high yield chickpea",
                "benefit_sharing": {
                    "type": BenefitSharingType.BOTH,
                    "details": "3% royalty on net sales, milestone payments at commercialization",
                    "royalty_rate": 3.0,
                    "milestones": [
                        {"event": "Variety registration", "amount": 50000, "currency": "INR"},
                        {"event": "First commercial sale", "amount": 100000, "currency": "INR"},
                    ],
                },
                "created_date": "2024-11-10",
                "signed_date": None,
                "effective_date": None,
                "expiry_date": None,
                "exchange_id": None,
            },
        ]

        for mta in demo_mtas:
            self.mtas[mta["id"]] = mta

    def get_templates(self) -> list:
        """Get all MTA templates"""
        return [
            {
                "id": t["id"],
                "name": t["name"],
                "type": t["type"],
                "description": t["description"],
                "version": t["version"],
                "clause_count": len(t["clauses"]),
                "benefit_sharing": t["benefit_sharing"],
                "duration_years": t["duration_years"],
                "requires_approval": t["requires_approval"],
            }
            for t in MTA_TEMPLATES.values()
        ]

    def get_template(self, template_id: str) -> Optional[dict]:
        """Get specific template with full clauses"""
        for t in MTA_TEMPLATES.values():
            if t["id"] == template_id:
                return t
        return None

    def create_mta(
        self,
        mta_type: MTAType,
        provider: dict,
        recipient: dict,
        accessions: list,
        crops: list,
        purpose: str,
        benefit_sharing: Optional[dict] = None,
        exchange_id: Optional[str] = None,
    ) -> dict:
        """Create a new MTA"""
        self.mta_counter += 1
        mta_number = f"MTA-{datetime.now().year}-{self.mta_counter:03d}"

        template = MTA_TEMPLATES.get(mta_type.value, MTA_TEMPLATES["institutional"])

        # Determine initial status
        if mta_type == MTAType.SMTA:
            status = MTAStatus.ACTIVE  # SMTA auto-approved
        else:
            status = MTAStatus.DRAFT

        # Calculate expiry if applicable
        expiry_date = None
        if template["duration_years"]:
            expiry_date = (datetime.now() + timedelta(days=365 * template["duration_years"])).strftime("%Y-%m-%d")

        mta = {
            "id": str(uuid4()),
            "mta_number": mta_number,
            "type": mta_type,
            "template_id": template["id"],
            "status": status,
            "provider": provider,
            "recipient": recipient,
            "accessions": accessions,
            "accession_count": len(accessions),
            "crops": crops,
            "purpose": purpose,
            "benefit_sharing": benefit_sharing or {
                "type": template["benefit_sharing"],
                "details": "",
            },
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "signed_date": datetime.now().strftime("%Y-%m-%d") if mta_type == MTAType.SMTA else None,
            "effective_date": datetime.now().strftime("%Y-%m-%d") if mta_type == MTAType.SMTA else None,
            "expiry_date": expiry_date,
            "exchange_id": exchange_id,
        }

        self.mtas[mta["id"]] = mta
        return mta

    def list_mtas(
        self,
        mta_type: Optional[MTAType] = None,
        status: Optional[MTAStatus] = None,
        institution: Optional[str] = None,
    ) -> list:
        """List MTAs with optional filters"""
        result = list(self.mtas.values())

        if mta_type:
            result = [m for m in result if m["type"] == mta_type]

        if status:
            result = [m for m in result if m["status"] == status]

        if institution:
            institution_lower = institution.lower()
            result = [
                m for m in result
                if institution_lower in m["provider"]["institution"].lower()
                or institution_lower in m["recipient"]["institution"].lower()
            ]

        return sorted(result, key=lambda x: x["created_date"], reverse=True)

    def get_mta(self, mta_id: str) -> Optional[dict]:
        """Get MTA by ID"""
        return self.mtas.get(mta_id)

    def get_mta_by_number(self, mta_number: str) -> Optional[dict]:
        """Get MTA by number"""
        for mta in self.mtas.values():
            if mta["mta_number"] == mta_number:
                return mta
        return None

    def submit_for_review(self, mta_id: str) -> Optional[dict]:
        """Submit MTA for review"""
        mta = self.mtas.get(mta_id)
        if not mta:
            return None

        if mta["status"] != MTAStatus.DRAFT:
            raise ValueError(f"Cannot submit MTA in {mta['status']} status")

        mta["status"] = MTAStatus.PENDING_REVIEW
        return mta

    def approve_mta(self, mta_id: str, approver: str) -> Optional[dict]:
        """Approve MTA after review"""
        mta = self.mtas.get(mta_id)
        if not mta:
            return None

        if mta["status"] != MTAStatus.PENDING_REVIEW:
            raise ValueError(f"Cannot approve MTA in {mta['status']} status")

        mta["status"] = MTAStatus.PENDING_SIGNATURE
        mta["approved_by"] = approver
        mta["approved_date"] = datetime.now().strftime("%Y-%m-%d")
        return mta

    def reject_mta(self, mta_id: str, reason: str, rejector: str) -> Optional[dict]:
        """Reject MTA"""
        mta = self.mtas.get(mta_id)
        if not mta:
            return None

        if mta["status"] not in [MTAStatus.PENDING_REVIEW, MTAStatus.PENDING_SIGNATURE]:
            raise ValueError(f"Cannot reject MTA in {mta['status']} status")

        mta["status"] = MTAStatus.REJECTED
        mta["rejection_reason"] = reason
        mta["rejected_by"] = rejector
        mta["rejected_date"] = datetime.now().strftime("%Y-%m-%d")
        return mta

    def sign_mta(self, mta_id: str, signatory: str) -> Optional[dict]:
        """Sign and activate MTA"""
        mta = self.mtas.get(mta_id)
        if not mta:
            return None

        if mta["status"] != MTAStatus.PENDING_SIGNATURE:
            raise ValueError(f"Cannot sign MTA in {mta['status']} status")

        mta["status"] = MTAStatus.ACTIVE
        mta["signed_by"] = signatory
        mta["signed_date"] = datetime.now().strftime("%Y-%m-%d")
        mta["effective_date"] = datetime.now().strftime("%Y-%m-%d")

        # Calculate expiry
        template = MTA_TEMPLATES.get(mta["type"].value if isinstance(mta["type"], MTAType) else mta["type"])
        if template and template["duration_years"]:
            mta["expiry_date"] = (datetime.now() + timedelta(days=365 * template["duration_years"])).strftime("%Y-%m-%d")

        return mta

    def terminate_mta(self, mta_id: str, reason: str, terminator: str) -> Optional[dict]:
        """Terminate an active MTA"""
        mta = self.mtas.get(mta_id)
        if not mta:
            return None

        if mta["status"] != MTAStatus.ACTIVE:
            raise ValueError(f"Cannot terminate MTA in {mta['status']} status")

        mta["status"] = MTAStatus.TERMINATED
        mta["termination_reason"] = reason
        mta["terminated_by"] = terminator
        mta["terminated_date"] = datetime.now().strftime("%Y-%m-%d")
        return mta

    def get_statistics(self) -> dict:
        """Get MTA statistics"""
        mtas = list(self.mtas.values())

        by_type = {}
        by_status = {}

        for mta in mtas:
            mta_type = mta["type"].value if isinstance(mta["type"], MTAType) else mta["type"]
            mta_status = mta["status"].value if isinstance(mta["status"], MTAStatus) else mta["status"]

            by_type[mta_type] = by_type.get(mta_type, 0) + 1
            by_status[mta_status] = by_status.get(mta_status, 0) + 1

        active_mtas = [m for m in mtas if (m["status"] == MTAStatus.ACTIVE or m["status"] == "active")]
        total_accessions = sum(m["accession_count"] for m in active_mtas)

        return {
            "total": len(mtas),
            "active": by_status.get("active", 0),
            "pending": by_status.get("pending_review", 0) + by_status.get("pending_signature", 0),
            "by_type": by_type,
            "by_status": by_status,
            "total_accessions_under_mta": total_accessions,
            "institutions": len(set(
                m["recipient"]["institution"] for m in mtas
            ) | set(
                m["provider"]["institution"] for m in mtas
            )),
        }

    def get_mta_for_exchange(self, exchange_id: str) -> Optional[dict]:
        """Get MTA associated with an exchange"""
        for mta in self.mtas.values():
            if mta.get("exchange_id") == exchange_id:
                return mta
        return None

    def check_compliance(self, mta_id: str) -> dict:
        """Check MTA compliance status"""
        mta = self.mtas.get(mta_id)
        if not mta:
            return {"error": "MTA not found"}

        issues = []
        warnings = []

        # Check expiry
        if mta.get("expiry_date"):
            expiry = datetime.strptime(mta["expiry_date"], "%Y-%m-%d")
            days_to_expiry = (expiry - datetime.now()).days

            if days_to_expiry < 0:
                issues.append("MTA has expired")
            elif days_to_expiry < 90:
                warnings.append(f"MTA expires in {days_to_expiry} days")

        # Check benefit sharing for commercial
        mta_type = mta["type"].value if isinstance(mta["type"], MTAType) else mta["type"]
        if mta_type == "commercial":
            bs = mta.get("benefit_sharing", {})
            if not bs.get("royalty_rate"):
                warnings.append("No royalty rate specified for commercial MTA")

        # Check status
        mta_status = mta["status"].value if isinstance(mta["status"], MTAStatus) else mta["status"]
        if mta_status not in ["active"]:
            issues.append(f"MTA is not active (status: {mta_status})")

        return {
            "mta_id": mta_id,
            "mta_number": mta["mta_number"],
            "compliant": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "checked_at": datetime.now().isoformat(),
        }


# Singleton instance
mta_service = MTAService()
