from src.common.models.domain import EmailData, AttachmentData, ShippingRecord, MatchResult
from src.common.models.contracts import (
    RawEmailReceived,
    EmailParsed,
    EmailClassified,
    RecordExtracted,
    RecordPersisted,
    MatchFound,
)

__all__ = [
    "EmailData",
    "AttachmentData",
    "ShippingRecord",
    "MatchResult",
    "RawEmailReceived",
    "EmailParsed",
    "EmailClassified",
    "RecordExtracted",
    "RecordPersisted",
    "MatchFound",
]
