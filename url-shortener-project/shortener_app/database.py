from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import get_settings

engine = create_engine(
    get_settings().db_url,
    connect_args={"check_same_thread": False}
    # SQLite allows more than one request at a time to communicate with db
)

# Create a working db session when you instantiate SessionLocal
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

# Returns a class that connect DB engine to SQLAlchemy Functionality
Base = declarative_base()