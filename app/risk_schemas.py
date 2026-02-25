"""
Pydantic schemas to score all the risks. 
Strong guardrail to explain the risks via: score + band + breakdown.
"""

from pydantic import BaseModel
from typing import Dict, List


class RiskOut(BaseModel):
    account_id: str
    risk_score: int
    risk_band: str               # Classify into LOW | MEDIUM | HIGH
    confidence: float            # How confident the model is: 0 - 1
    score_breakdown: Dict[str, int]  # Scores which signal
    fired_signals: List[str]         # Which signal was fired