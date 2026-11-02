"""
SQLAlchemy 2.x async-compatible database setup.

Exports:
  - engine        : SQLAlchemy Engine (synchronous, psycopg v3)
  - Base          : Declarative base for all ORM models
  - get_db        : FastAPI dependency yielding a Session per request
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # detect stale connections before use
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,  # log SQL only in debug mode
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Declarative base (shared by all models)
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Project-wide declarative base.

    All ORM model classes must inherit from this Base so that Alembic's
    autogenerate can discover them via ``Base.metadata``.
    """
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy Session and guarantee it is closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
