"""
Pydantic schemas for feedback loop summary output.
"""

from pydantic import BaseModel
from typing import Dict, List, Optional


class OverridePattern(BaseModel):
    ai_path: str            # What the AI recommended
    human_path: str        # What the analyst/human changed it to
    count: int                # How many times this pattern occurred
    example_reasons: List[str]       # Sample analyst reasons for this override


class SignalOverrideRate(BaseModel):
    signal_name: str
    total_cases: int          # How many cases this signal appeared in
    override_count: int        # How many of those were overridden
    override_rate_pct: float       # override_count / total_cases * 100


class ConfidenceGapSummary(BaseModel):
    avg_gap: float           # Average gap between det and AI confidence
    high_gap_count: int     # Cases where gap > 0.3 (worth investigating)
    high_gap_threshold: float = 0.3


class FeedbackSummaryOut(BaseModel):
    total_actions: int           # Total analyst actions recorded
    total_overrides: int         # Total OVERRIDE actions
    override_rate_pct: float        # overall override rate
    override_patterns: List[OverridePattern]    # AI path → human path breakdown
    signal_override_rates: List[SignalOverrideRate]  # Per-signal override rates
    confidence_gap_summary: ConfidenceGapSummary
    recommendation: Optional[str]      # Auto-generated recommendation based on patterns
















