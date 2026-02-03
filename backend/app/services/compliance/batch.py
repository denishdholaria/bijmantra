import asyncio
import zipfile
import io
import os
import functools
from datetime import datetime
from typing import List
from app.schemas.compliance import SeedBatchInfo, ComplianceType
from app.services.compliance.pdf_generator import generate_certificate_pdf, calculate_hash
from app.services.compliance.email_service import send_email_with_attachment
from app.services.task_queue import task_queue, TaskPriority

# Directory for storing generated files temporarily
OUTPUT_DIR = "generated_certificates"
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def process_batch_generation(
    compliance_type: ComplianceType,
    batches: List[SeedBatchInfo],
    issuer_name: str,
    email_to: str,
    progress_callback=None
):
    """
    Background task to generate certificates for a batch of seeds.
    """
    total = len(batches)
    pdf_files = []

    loop = asyncio.get_running_loop()

    # Use consistent issue date for the whole batch job
    issue_date = datetime.now()

    for i, batch in enumerate(batches):
        if progress_callback:
            progress_callback(i / total, f"Generating certificate {i+1}/{total}")

        cert_hash = calculate_hash(batch, compliance_type)

        # Verification URL (mock)
        verification_url = f"https://bijmantra.org/verify/{cert_hash}"

        # Run PDF generation in thread pool to avoid blocking
        pdf_bytes = await loop.run_in_executor(
            None,
            functools.partial(
                generate_certificate_pdf,
                batch=batch,
                compliance_type=compliance_type,
                issuer_name=issuer_name,
                certificate_hash=cert_hash,
                verification_url=verification_url,
                issue_date=issue_date
            )
        )

        filename = f"{batch.batch_id}_{cert_hash[:8]}.pdf"
        filepath = os.path.join(OUTPUT_DIR, filename)

        # Writing to file is also blocking I/O, ideally should be async or in executor.
        # But for simplicity let's keep it direct or put in executor.
        # Since we are already in executor for PDF gen, we could have done write there too,
        # but generate_certificate_pdf returns bytes.
        # Let's put write in executor too.

        def write_file(path, data):
            with open(path, "wb") as f:
                f.write(data)

        await loop.run_in_executor(None, write_file, filepath, pdf_bytes)

        pdf_files.append((filename, filepath))

        # Simulate some work
        await asyncio.sleep(0.01)

    if progress_callback:
        progress_callback(0.9, "Creating ZIP archive...")

    # Create ZIP
    zip_filename = f"certificates_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
    zip_filepath = os.path.join(OUTPUT_DIR, zip_filename)

    def create_zip():
        with zipfile.ZipFile(zip_filepath, 'w') as zipf:
            for fname, fpath in pdf_files:
                zipf.write(fpath, fname)

    await loop.run_in_executor(None, create_zip)

    if progress_callback:
        progress_callback(0.95, "Sending email...")

    # Send Email
    await send_email_with_attachment(
        to_email=email_to,
        subject="Your Batch Compliance Certificates",
        body=f"Please find attached the certificates for {total} seed batches.",
        attachment_path=zip_filepath
    )

    if progress_callback:
        progress_callback(1.0, "Done")

    return {"zip_path": zip_filepath, "count": total}

async def submit_batch_job(
    compliance_type: ComplianceType,
    batches: List[SeedBatchInfo],
    issuer_name: str,
    email_to: str
) -> str:
    task_id = await task_queue.submit(
        name="batch_certificate_generation",
        func=process_batch_generation,
        kwargs={
            "compliance_type": compliance_type,
            "batches": batches,
            "issuer_name": issuer_name,
            "email_to": email_to
        },
        priority=TaskPriority.NORMAL
    )
    return task_id
