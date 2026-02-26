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
SLA_BY_PATH_HOURS = {
    "ESCALATE": 2,
    "REVIEW": 24,
    "REQUEST_INFO": 48,
    # MONITOR has no strict SLA, just to recheck later
}

# Mark as DUE_SOON if due in <= 2 hours
DUE_SOON_HOURS = 2  #set default to 2 hours


#SLA fields for case: sla due at and sla status
def assign_sla(created_at: datetime, routed_path: str) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    # MONITOR: no strict  SLA
    if routed_path == "MONITOR":
        return {"sla_due_at": None, "sla_status": "NO_SLA"}

    hours = SLA_BY_PATH_HOURS.get(routed_path, 24)  # default to 24h if unknown
    sla_due_at = created_at + timedelta(hours=hours)

    # Determine status
    if now > sla_due_at:
        status = "BREACHED"
    else:
        time_left = sla_due_at - now
        if time_left <= timedelta(hours=DUE_SOON_HOURS):
            status = "DUE_SOON"
        else:
            status = "ON_TRACK"

    return {"sla_due_at": sla_due_at, "sla_status": status}