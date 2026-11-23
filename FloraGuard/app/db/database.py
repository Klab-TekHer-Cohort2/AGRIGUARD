"""Database initialization and session management."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Find the main FloraGuard project folder
BASE_DIR = Path(__file__).resolve().parents[2]

# Store our SQLite database in the project folder
DATABASE_PATH = BASE_DIR / "floraguard.db"

# Create the database connection
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# Create database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for our database tables
class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create all tables if they do not exist.

    Safe to call repeatedly; does not drop or alter existing data.
    """
    # Import models so they register with Base.metadata
    from app.db import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    """Provide a database session to API endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()