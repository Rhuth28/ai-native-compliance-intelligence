"""
Database models which defines how events are stored.
"""

# Import dependencies
from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from .database import Base


class Event(Base):
    """
    Represents a raw operational event.The full payload is stored for traceability.
    """

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)
    account_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    payload = Column(JSON)  # Full raw event payload