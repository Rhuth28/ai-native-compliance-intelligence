"""
Risk scoring engine. Guardrails for auditability:
- Deterministic and explainable.
- Scores are derived from signals with simple weights.
- Provide a "score_breakdown" so analysts can see why the score is what it is.
"""

from typing import Dict, Any, List, Tuple

# Define the weight of each signal
SIGNAL_WEIGHTS: Dict[str, int] = {
    "NEW_DEVICE_LOGIN": 25,
    "PROFILE_CHANGE": 15,
    "LARGE_TRANSACTION": 25,
    "NEW_PAYEE_LARGE_TRANSFER": 30,
    "PROFILE_CHANGE_AND_TRANSFER_24H": 35,
}


# Define the band thresholds
# 0-39 = LOW, 40-69 = MEDIUM, 70+ = HIGH
LOW_MAX = 39
MEDIUM_MAX = 69


# Convert the signals to a score, and return total score, breakdown and which signal(s) was fired
def score_signals(signals: List[Dict[str, Any]]) -> Tuple[int, Dict[str, int], List[str]]:
    
    breakdown: Dict[str, int] = {}
    fired: List[str] = []  # for each fired signal

    #Loop through each signal and its weight
    for s in signals:
        name = s.get("signal_name", "UNKNOWN_SIGNAL")   # if the signal is unknown--to prevent crashes
        points = SIGNAL_WEIGHTS.get(name, 5)  # Unknown signals will be assigned small default weight

        # Add the weight for each signal that occurred to breakdown dict
        breakdown[name] = breakdown.get(name, 0) + points  #Duplicate signals will increase score
        fired.append(name)   #Collect all the signals that was fired

    total_score = sum(breakdown.values())  #Sums all weight
    fired_deduped = sorted(list(set(fired)))   # Sort the fired list incase to return unique signals
    return total_score, breakdown, fired_deduped


#convert a score into a band which will determine routing
def band_from_score(score: int) -> str:
    if score <= LOW_MAX:
        return "LOW"
    if score <= MEDIUM_MAX:
        return "MEDIUM"
    return "HIGH"


# Confidence that highlights similar signals
def confidence_heuristic(score: int, fired_signal_count: int) -> float:
   
    if fired_signal_count == 0:  # No signal mean 0 confidence
        return 0.0

    # Convert the score to max of 1...confidence shouldn't exceed 1
    score_component = min(score, 100) / 100.0

    # Max all signal count to 4. More signals isn't really more confident
    count_component = min(fired_signal_count, 4) / 4.0

    # How severe the confidence score is vs how many signals were sent
    confidence = (0.6 * score_component) + (0.4 * count_component)  # Severity should be more than how many signals

    # Confidence should never go below 0 or above 1
    return round(max(0.0, min(1.0, confidence)), 2)


# function to assess risk
def assess_risk(account_id: str, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main function that takes account_id + signals and outputs risk assessment.
    """
    score, breakdown, fired = score_signals(signals)
    band = band_from_score(score)
    confidence = confidence_heuristic(score=score, fired_signal_count=len(fired))

    return {
        "account_id": account_id,
        "risk_score": score,
        "risk_band": band,
        "confidence": confidence,
        "score_breakdown": breakdown,
        "fired_signals": fired,
    }