from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.common.config import settings

_sync_db_url = settings.database_url.replace("+asyncpg", "")
sync_engine = create_engine(_sync_db_url, pool_size=5, max_overflow=10)
SyncSession = sessionmaker(bind=sync_engine, class_=Session)


def get_sync_db() -> Session:
    session = SyncSession()
    try:
        return session
    except Exception:
        session.close()
        raise
