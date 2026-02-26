"""
SLA (Service Level Agreement)
What this does is:
- Make the system operational, especially if account needs freezing or SAR needs to be filed immediately.
- Assign deadlines based on workflow path.
- Compute SLA status (on track / due soon / breached).
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any

# SLA rules by routed workflow path
# Hours allowed before breach
SLA_BY_PATH_HOURS = {
    "ESCALATE": 2,
    "REVIEW": 24,
    "REQUEST_INFO": 48,
    # MONITOR has no strict SLA, analyst can recheck anytime
}

# If due within <= 2 hours, mark as DUE_SOON
DUE_SOON_HOURS = 2


#SLA compute fields for case: sla due at and sla status of on_track, due_soon, breached or no_sla
def assign_sla(created_at: datetime, routed_path: str) -> Dict[str, Any]:

    # Current time in UTC (timezone-aware)
    now = datetime.now(timezone.utc)

    # If case is MONITOR, no hard SLA
    if routed_path == "MONITOR":
        return {"sla_due_at": None, "sla_status": "NO_SLA"}

    # ---- Normalize created_at ----
    # convert db time to UTC
    if created_at is not None and created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    # Determine SLA duration
    hours = SLA_BY_PATH_HOURS.get(routed_path, 24)  # default 24h fallback

    # Compute due time
    sla_due_at = created_at + timedelta(hours=hours)

    # ---- Determine status ----
    if now > sla_due_at:
        status = "BREACHED"
    else:
        time_left = sla_due_at - now

        if time_left <= timedelta(hours=DUE_SOON_HOURS):
            status = "DUE_SOON"
        else:
            status = "ON_TRACK"

    return {
        "sla_due_at": sla_due_at,
        "sla_status": status
    }