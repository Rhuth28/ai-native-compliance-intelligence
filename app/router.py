"""
This routes the case and implements strong guardrails
Its purpose is to:
- Bound AI autonomy safely.
- Convert the AI output into a final "routed_path" that will be used by operations/SLA.
The guardrails are:
- If AI confidence is low - force Human REVIEW
- If risk is HIGH and AI says MONITOR - force human REVIEW
- ESCALATE always requires that a human analyst confirms
"""

from typing import Dict, Any

CONFIDENCE_FLOOR = 0.65  # routing of anything below this won't be trusted


#Function to apply guardrails. Returns routed path, guardrail notes (What changed and why) and if it needs human confirmation(escalation)
def apply_guardrails(ai_output: Dict[str, Any], risk_band: str) -> Dict[str, Any]:
    routed_path = ai_output.get("workflow_path", "REVIEW")
    confidence = float(ai_output.get("confidence", 0.0))

    notes = []

    # Guardrail 1: low confidence = REVIEW
    if confidence < CONFIDENCE_FLOOR:
        if routed_path != "REVIEW":
            notes.append(f"Confidence {confidence} below {CONFIDENCE_FLOOR}; forcing REVIEW.")
        routed_path = "REVIEW"

    # Guardrail 2: High risk = REVIEW, when AI says to monitor, as a human needs to check it
    if risk_band == "HIGH" and routed_path == "MONITOR":
        notes.append("Risk band is HIGH. Forcing REVIEW.")
        routed_path = "REVIEW"
    needs_human_confirmation = (routed_path == "ESCALATE")

    return {
        **ai_output,
        "routed_path": routed_path,
        "guardrail_notes": notes,
        "needs_human_confirmation": needs_human_confirmation,
    }