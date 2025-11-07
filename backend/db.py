# backend/db.py
"""
Database configuration for Delta Cargo system.
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Use SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cargo.db")

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Enable foreign keys for SQLite
    # @event.listens_for(engine, "connect")
   # def set_sqlite_pragma(dbapi_conn, connection_record):
       # cursor = dbapi_conn.cursor()
        #cursor.execute("PRAGMA foreign_keys=ON")
      #  cursor.close()
    
    print(f"[DB] Using SQLite: {DATABASE_URL}")
else:
    # PostgreSQL for production
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
    print("[DB] Using PostgreSQL")

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def initialize_database():
    """Initialize database tables."""
    from . import models
    
    try:
        Base.metadata.create_all(bind=engine)
        print("[DB] вњ… Database tables created")
        
        with engine.connect() as connection:
            print("[DB] вњ… Database connection verified")
            
    except Exception as e:
        print(f"[DB] вќЊ Error: {e}")
        raise


def close_database():
    """Close database connections."""
    try:
        engine.dispose()
        print("[DB] Database connections closed")
    except Exception as e:
        print(f"[DB] Error closing database: {e}")


def check_database_health():
    """Health check."""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"[DB] Health check failed: {e}")
        return False


def get_database_info():
    """Get database info."""
    db_type = "SQLite" if DATABASE_URL.startswith("sqlite") else "PostgreSQL"
    return {
        "type": db_type,
        "url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL
    }