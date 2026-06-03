# PROMPT: Load a POS CSV into a pos_transactions table
# CHANGES MADE: Created POSTransaction model

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from .base import Base

class POSTransaction(Base):
    __tablename__ = "pos_transactions"
    transaction_id = Column(String, primary_key=True)   # invoice_number
    store_id       = Column(String, ForeignKey("stores.id"), nullable=False)
    timestamp_utc  = Column(DateTime(timezone=True), nullable=False)
    basket_value   = Column(Float, nullable=False)
    line_count     = Column(Integer, nullable=False)
    quantity       = Column(Integer, nullable=False)
