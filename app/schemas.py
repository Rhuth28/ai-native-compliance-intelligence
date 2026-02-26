"""
Pydantic schemas to validate all requests and ensure they have the required structure.
"""

from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime


class EventCreate(BaseModel):
    event_type: str
    account_id: str
    event_timestamp: datetime
    payload: Dict[str, Any]