import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_engine = None
_SessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        from psycopg2.extras import RealDictCursor
        _engine = create_engine(
            os.environ["DATABASE_URL"],
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args={"cursor_factory": RealDictCursor}
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
