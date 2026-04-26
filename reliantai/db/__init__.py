import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_engine = None
_SessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        # Production-grade pool configuration via environment variables
        pool_size = int(os.environ.get("DB_POOL_SIZE", "10"))
        max_overflow = int(os.environ.get("DB_POOL_MAX_OVERFLOW", "20"))
        pool_timeout = int(os.environ.get("DB_POOL_TIMEOUT", "30"))
        pool_recycle = int(os.environ.get("DB_POOL_RECYCLE", "3600"))

        _engine = create_engine(
            os.environ["DATABASE_URL"],
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
        )
    return _engine


def _get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=_get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


@contextmanager
def get_db_session():
    SessionLocal = _get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
