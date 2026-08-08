from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# The engine: SQLAlchemy's core connection to Postgres.
# It manages a pool of connections under the hood.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,          # persistent connections kept open (was default 5)
    max_overflow=40,       # extra connections allowed under burst (was default 10)
    pool_timeout=30,       # seconds to wait for a connection before erroring
)

# A session factory. Each request/task gets its own session (unit of work)
# to run queries and commit changes.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# The declarative base. Every model class inherits from this; it's how
# SQLAlchemy knows which classes map to tables.
Base = declarative_base()


def get_db():
    """Yield a database session, guaranteeing it's closed afterward.
    Used as a FastAPI dependency so each request gets a fresh session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()