"""
database.py
============
SQLAlchemy engine, session factory and declarative base for the SQLite
persistence layer. SQLite is intentionally used here (per the project spec)
because PurpleLab AI is a single-user, single-host lab tool - no need for a
client/server database.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a DB session and guarantees closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Called once at application startup."""
    from app.models import scenario_run, event, report  # noqa: F401  (ensure models are registered)

    Base.metadata.create_all(bind=engine)
