from fastapi import APIRouter, Depends, status

from src.api.deps import get_optional_user
from src.api.schemas.email import InboundEmailRequest, InboundEmailResponse
from src.common.db.models import User
from src.common.models.contracts import RawEmailReceived
from src.common.messaging.publishers import publish_raw_email_received
from src.common.observability.metrics import email_received, email_bytes
from src.common.observability.tracing import get_correlation_id

router = APIRouter(prefix="/inbound", tags=["inbound"])


@router.post("/email", response_model=InboundEmailResponse, status_code=status.HTTP_202_ACCEPTED)
async def receive_inbound_email(
    payload: InboundEmailRequest,
    current_user: User | None = Depends(get_optional_user),
) -> InboundEmailResponse:
    from uuid import uuid4

    email_id = uuid4()
    event = RawEmailReceived(
        email_id=email_id,
        message_id=payload.message_id,
        source=payload.source or "smtp",
        sender=payload.sender,
        recipients=payload.recipients,
        received_at=payload.received_at,
        subject=payload.subject,
        body_text=payload.body_text,
        body_html=payload.body_html,
        headers=payload.headers,
    )
    publish_raw_email_received(event.model_dump(mode="json"))

    email_received.labels(source=payload.source or "smtp").inc()
    if payload.body_text:
        email_bytes.observe(len(payload.body_text.encode()))

    return InboundEmailResponse(
        email_id=email_id,
        status="accepted",
        correlation_id=get_correlation_id(),
    )
