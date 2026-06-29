"""Database connection and session management for ReliantAI."""

import os
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://reliantai_dev:reliantai_dev@localhost:5433/reliantai"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.environ.get("SQL_ECHO", "false").lower() == "true"
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Initialize database and run migrations."""
    with get_db_session() as db:
        db.execute(text("SELECT 1"))
