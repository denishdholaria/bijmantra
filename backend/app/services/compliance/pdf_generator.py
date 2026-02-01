import os
from jinja2 import Environment, FileSystemLoader
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    HTML = None
    WEASYPRINT_AVAILABLE = False
from app.schemas.compliance import SeedBatchInfo, ComplianceType
from datetime import datetime
import hashlib

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def generate_certificate_pdf(
    batch: SeedBatchInfo,
    compliance_type: ComplianceType,
    issuer_name: str,
    certificate_hash: str,
    verification_url: str,
    issue_date: datetime = None,
    notes: str = None
) -> bytes:
    template = env.get_template("certificate.html")

    if issue_date is None:
        issue_date = datetime.now()

    html_content = template.render(
        batch=batch,
        compliance_type=compliance_type.value,
        issuer_name=issuer_name,
        certificate_hash=certificate_hash,
        verification_url=verification_url,
        notes=notes,
        issue_date=issue_date.strftime("%Y-%m-%d")
    )

    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError("PDF generation requires weasyprint with Pango. Install with: brew install pango")
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes

def calculate_hash(batch: SeedBatchInfo, compliance_type: ComplianceType) -> str:
    # Create a unique string based on batch data and timestamp
    data_string = f"{batch.model_dump_json()}-{compliance_type}-{datetime.now().isoformat()}"
    return hashlib.sha256(data_string.encode()).hexdigest()
