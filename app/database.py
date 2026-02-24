"""
Database configuration.
Using SQLite for simplicity (easy to demo and explain).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite file-based DB
DATABASE_URL = "sqlite:///./compliance.db"

# Engine manages connection pool
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  #SQLite
)

# Session factory (for each request)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()