import asyncio

async def send_email_with_attachment(
    to_email: str,
    subject: str,
    body: str,
    attachment_path: str
):
    # Mock email sending
    print(f"MOCK EMAIL TO: [{to_email}]")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    print(f"Attachment: {attachment_path}")
    # Simulate network delay
    await asyncio.sleep(1)
    return True
