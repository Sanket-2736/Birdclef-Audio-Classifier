
"""
SQLAlchemy database setup with connection pooling and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from .config import get_settings


print("\n[DEBUG] Initializing SQLAlchemy database configuration...")

settings = get_settings()

# Create database URL
DATABASE_URL = settings.DATABASE_URL

print(f"[DEBUG] Database URL: {DATABASE_URL}")


# Create engine
print("\n[DEBUG] Creating SQLAlchemy database engine...")

if DATABASE_URL.startswith("sqlite"):

    print("[DEBUG] SQLite database detected.")
    print("[DEBUG] Applying SQLite connection configuration.")
    print("[DEBUG] check_same_thread: False")
    print("[DEBUG] Connection pool: StaticPool")

    # SQLite configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

else:

    print("[DEBUG] Non-SQLite database detected.")
    print("[DEBUG] Applying standard database configuration.")
    print("[DEBUG] pool_pre_ping: True")

    # PostgreSQL or other database
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

print("[SUCCESS] SQLAlchemy engine created successfully.")
print(f"[DEBUG] Engine dialect: {engine.dialect.name}")
print(f"[DEBUG] Engine driver: {engine.dialect.driver}")
print(f"[DEBUG] Engine pool: {type(engine.pool).__name__}")


# Create session factory
print("\n[DEBUG] Creating SQLAlchemy session factory...")

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

print("[SUCCESS] SessionLocal created successfully.")
print("[DEBUG] autocommit: False")
print("[DEBUG] autoflush: False")


# Base class for models
print("\n[DEBUG] Creating SQLAlchemy declarative base...")

Base = declarative_base()

print("[SUCCESS] SQLAlchemy declarative base initialized.")


def get_db():
    """
    Dependency to get database session.

    Usage:
        from .db import get_db
        from sqlalchemy.orm import Session

        @app.get("/")
        def read_root(db: Session = Depends(get_db)):
            ...
    """

    print("\n[DEBUG] get_db() called")
    print("[DEBUG] Creating a new database session...")

    db = SessionLocal()

    print("[SUCCESS] Database session created successfully.")

    try:

        print("[DEBUG] Yielding database session to request handler.")

        yield db

        print("[DEBUG] Request handler completed.")

    finally:

        print("[DEBUG] Closing database session...")

        db.close()

        print("[SUCCESS] Database session closed successfully.")


def init_db():
    """Create all tables."""

    print("\n" + "=" * 60)
    print("[DEBUG] DATABASE INITIALIZATION STARTED")
    print("=" * 60)

    print(f"[DEBUG] Database dialect: {engine.dialect.name}")
    print("[DEBUG] Checking registered SQLAlchemy models...")

    registered_tables = list(Base.metadata.tables.keys())

    print(f"[DEBUG] Registered tables: {registered_tables}")
    print(f"[DEBUG] Total registered tables: {len(registered_tables)}")

    print("\n[DEBUG] Creating database tables if they do not exist...")

    Base.metadata.create_all(bind=engine)

    print("[SUCCESS] Database table initialization completed.")

    print("\n[DEBUG] Verifying database tables...")

    existing_tables = list(Base.metadata.tables.keys())

    for table_name in existing_tables:
        print(f"[DEBUG] Registered table: {table_name}")

    print(f"[SUCCESS] Total registered tables: {len(existing_tables)}")

    print("\n" + "=" * 60)
    print("[SUCCESS] DATABASE INITIALIZATION FINISHED")
    print("=" * 60)


print("\n[SUCCESS] Database module loaded successfully.")
