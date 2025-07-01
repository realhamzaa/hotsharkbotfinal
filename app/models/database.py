"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import Config

# Create database engine
engine = create_engine(
    Config.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in Config.DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db():
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Create all tables in the database
    """
    Base.metadata.create_all(bind=engine)



from app.models.market_data import MarketData, IndicatorData, Signal


