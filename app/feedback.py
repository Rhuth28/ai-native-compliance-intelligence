"""
Feedback Loop that reads analyst override data and patterns.
This closes the loop between:
- What the AI decided
- What the human changed it to
- The reason

Output is used to:
- Identify over/under-routing patterns
- Flag signals with high override rates
- Surface confidence gap anomalies
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from .actions import CaseAction
from .feedback_schemas import (
    FeedbackSummaryOut,
    OverridePattern,
    SignalOverrideRate,
    ConfidenceGapSummary,
)

# If override rate exceeds this
OVERRIDE_RATE_ALERT_THRESHOLD = 0.30  # 30%

# If confidence gap is more, flag
HIGH_GAP_THRESHOLD = 0.3


def get_feedback_summary(db: Session) -> FeedbackSummaryOut:

    # ---- Fetch all analyst actions (excluding the AUTO_ROUTED entries) ----
    all_actions = (
        db.query(CaseAction)
        .filter(CaseAction.action != "AUTO_ROUTED")
        .all()
    )

    total_actions = len(all_actions)
    overrides = [a for a in all_actions if a.action == "OVERRIDE"]
    total_overrides = len(overrides)
    override_rate_pct = round((total_overrides / total_actions * 100), 1) if total_actions > 0 else 0.0

    # ---- Override patterns: AI path to human path ----
    pattern_map: Dict[str, Dict[str, Any]] = {}

    for o in overrides:
        extra = o.extra_data or {}
        ai_path = extra.get("ai_routed_path") or extra.get("previous_routed_path") or "UNKNOWN"
        human_path = extra.get("human_final_path") or "UNKNOWN"
        reason = o.reason or ""

        key = f"{ai_path}→{human_path}"
        if key not in pattern_map:
            pattern_map[key] = {
                "ai_path": ai_path,
                "human_path": human_path,
                "count": 0,
                "example_reasons": [],
            }
        pattern_map[key]["count"] += 1

        # Collect up to 3 example reasons per pattern
        if reason and len(pattern_map[key]["example_reasons"]) < 3:
            pattern_map[key]["example_reasons"].append(reason)

    override_patterns = [
        OverridePattern(**v)
        for v in sorted(pattern_map.values(), key=lambda x: x["count"], reverse=True)
    ]

    # ---- Signal override rates ----
    # Map signal_name - {total_cases, override_count}
    signal_map: Dict[str, Dict[str, int]] = {}

    # Count total cases per signal from AUTO_ROUTED entries
    auto_routed = (
        db.query(CaseAction)
        .filter(CaseAction.action == "AUTO_ROUTED")
        .all()
    )

    for ar in auto_routed:
        extra = ar.extra_data or {}
        signals = extra.get("fired_signals", [])
        for sig in signals:
            if sig not in signal_map:
                signal_map[sig] = {"total_cases": 0, "override_count": 0}
            signal_map[sig]["total_cases"] += 1

    # Count overrides per signal
    for o in overrides:
        extra = o.extra_data or {}
        signals = extra.get("fired_signals", [])
        for sig in signals:
            if sig not in signal_map:
                signal_map[sig] = {"total_cases": 0, "override_count": 0}
            signal_map[sig]["override_count"] += 1

    signal_override_rates = [
        SignalOverrideRate(
            signal_name=sig,
            total_cases=vals["total_cases"],
            override_count=vals["override_count"],
            override_rate_pct=round(
                vals["override_count"] / vals["total_cases"] * 100, 1
            ) if vals["total_cases"] > 0 else 0.0,
        )
        for sig, vals in sorted(signal_map.items(), key=lambda x: x[1]["override_count"], reverse=True)
    ]

    # ---- Confidence gap summary ----
    gaps = []
    for ar in auto_routed:
        extra = ar.extra_data or {}
        gap = extra.get("confidence_gap")
        if gap is not None:
            try:
                gaps.append(float(gap))
            except (ValueError, TypeError):
                pass

    avg_gap = round(sum(gaps) / len(gaps), 3) if gaps else 0.0
    high_gap_count = sum(1 for g in gaps if g > HIGH_GAP_THRESHOLD)

    confidence_gap_summary = ConfidenceGapSummary(
        avg_gap=avg_gap,
        high_gap_count=high_gap_count,
        high_gap_threshold=HIGH_GAP_THRESHOLD,
    )

    # ---- Auto-generate recommendation ----
    recommendation = None

    if override_rate_pct >= OVERRIDE_RATE_ALERT_THRESHOLD * 100:
        recommendation = (
            f"Override rate is {override_rate_pct}% — above the {int(OVERRIDE_RATE_ALERT_THRESHOLD * 100)}% threshold. "
            "Review the most common override patterns and consider adjusting signal weights or the system prompt."
        )
    elif high_gap_count > 5:
        recommendation = (
            f"{high_gap_count} cases had a confidence gap above {HIGH_GAP_THRESHOLD}. "
            "Deterministic and AI confidence are frequently misaligned — review scoring weights."
        )
    elif total_overrides == 0 and total_actions > 10:
        recommendation = "No overrides recorded. Either the system is performing well or analysts are not reviewing closely enough."

    return FeedbackSummaryOut(
        total_actions=total_actions,
        total_overrides=total_overrides,
        override_rate_pct=override_rate_pct,
        override_patterns=override_patterns,
        signal_override_rates=signal_override_rates,
        confidence_gap_summary=confidence_gap_summary,
        recommendation=recommendation,
    )