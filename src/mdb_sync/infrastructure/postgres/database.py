from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.mdb_sync.config import settings
from src.mdb_sync.infrastructure.postgres.models import Base

engine = create_engine(settings.postgres_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Ensures all tables exist in the database."""
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
