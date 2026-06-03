# PROMPT: Add a sessions table for session-level deduplication
# CHANGES MADE: Created Session model

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from .base import Base

class Session(Base):
    __tablename__ = "sessions"
    visitor_id   = Column(String, primary_key=True)
    store_id     = Column(String, ForeignKey("stores.id"), nullable=False)
    first_seen   = Column(DateTime(timezone=True))
    last_seen    = Column(DateTime(timezone=True))
    is_staff     = Column(Boolean, default=False)
    re_entry     = Column(Boolean, default=False)
    converted    = Column(Boolean, default=False)
    entry_count  = Column(Integer, default=0)
