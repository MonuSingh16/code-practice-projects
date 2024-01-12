from sqlalchemy import Column, Boolean, Integer, String

from .database import Base

# Singular Name of Model
# Database table name to be plural
class URL(Base):
    __tablename__ = "url"

    id = Column(Integer, primary_key=True) # primary key, hence no need for unique argument
    key = Column(String, unique=True, index=True)
    secret_key = Column(String, unique=True, index=True)
    target_url = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    clicks = Column(Integer, default=0)
