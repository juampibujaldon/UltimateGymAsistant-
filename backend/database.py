"""
Database configuration.
Sets up the SQLAlchemy engine, session factory, and base declarative class.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()


def normalize_database_url(url: str) -> str:
    """Normalize provider-specific URLs into a SQLAlchemy-compatible format."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


# SQLite database file path from env or default
SQLALCHEMY_DATABASE_URL = normalize_database_url(
    os.getenv("DATABASE_URL", "sqlite:///./gym_coach.db")
)

# engine configuration
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
)

# Each request gets its own session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db():
    """Dependency that provides a database session and ensures it's closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
