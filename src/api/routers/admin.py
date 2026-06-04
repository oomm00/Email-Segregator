from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.api.schemas.email import AdminUploadResponse
from src.common.audit import log_audit
from src.common.db.models import RawEmail, EmailAttachment, User
from src.common.db.session import get_db
from src.common.messaging.publishers import publish_raw_email_received
from src.common.models.contracts import RawEmailReceived
from src.common.storage.minio_client import storage

router = APIRouter(tags=["admin"])


@router.post("/email/upload", response_model=AdminUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def admin_upload_email(
    file: UploadFile = File(...),
    source: str = Form("upload"),
    subject: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename required")

    content = await file.read()
    email_id = uuid4()
    storage_path = f"{email_id}/{file.filename}"

    await storage.upload(storage_path, content, file.content_type or "application/octet-stream")

    email = RawEmail(
        id=email_id,
        message_id=f"<upload-{email_id}>",
        subject=subject or file.filename,
        sender=current_user.email,
        recipients=current_user.email,
        body_text=f"Admin upload: {file.filename} ({len(content)} bytes)",
        received_at=datetime.utcnow(),
        source=source,
        status="received",
    )
    db.add(email)

    attachment = EmailAttachment(
        id=uuid4(),
        email_id=email_id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        size=len(content),
        storage_path=storage_path,
        storage_bucket="shipping-attachments",
    )
    db.add(attachment)
    await db.flush()

    await log_audit(db, "email.uploaded", "raw_email", str(email_id), actor_id=current_user.id,
                    payload={"filename": file.filename, "size": len(content)})

    event = RawEmailReceived(
        email_id=email_id,
        message_id=email.message_id,
        source=source,
        sender=email.sender,
        recipients=[email.recipients],
        received_at=email.received_at,
        subject=email.subject,
        body_text=email.body_text,
    )
    publish_raw_email_received(event.model_dump(mode="json"))

    return AdminUploadResponse(
        email_id=email_id,
        filename=file.filename,
        size=len(content),
        status="accepted",
    )
