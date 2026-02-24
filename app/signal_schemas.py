"""
Pydantic schemas that will signal outputs.
"""

from pydantic import BaseModel
from typing import List


class SignalOut(BaseModel):
    signal_name: str
    why_it_fired: str
    evidence_event_ids: List[int]