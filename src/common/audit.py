from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.db.models import AuditLog


async def log_audit(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: str,
    actor_id: Optional[UUID] = None,
    payload: Optional[dict[str, Any]] = None,
) -> AuditLog:
    entry = AuditLog(
        id=uuid4(),
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        actor_id=actor_id,
        payload=payload,
    )
    db.add(entry)
    await db.flush()
    return entry
