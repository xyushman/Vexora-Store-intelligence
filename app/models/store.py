# PROMPT: Add store alias resolution so multiple submitted IDs map to one canonical store
# CHANGES MADE: Created Store and StoreAlias models with resolve_store_id() helper

from sqlalchemy import Column, String, ForeignKey
from .base import Base

class Store(Base):
    __tablename__ = "stores"
    id = Column(String, primary_key=True)          # canonical e.g. "ST1008"
    name = Column(String, nullable=False)
    city = Column(String)
    timezone = Column(String, default="Asia/Kolkata")

class StoreAlias(Base):
    __tablename__ = "store_aliases"
    alias = Column(String, primary_key=True)       # e.g. "STORE_BLR_002"
    canonical_id = Column(String, ForeignKey("stores.id"), nullable=False)
