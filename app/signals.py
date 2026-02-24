"""
Signal extraction engine. The goal is:
- Convert raw events into explainable signals.
- Output the signals with event IDs as evidence so that a human can verify and make informed decisions.
"""


# Import dependencies
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .models import Event

# Define thresholds
LARGE_TXN_THRESHOLD = 3000 # This is in CAD
LOOKBACK_DAYS = 30  # How far back in (days) the AI should check for
PROFILE_CHANGE_WINDOW = 24  # Check if profile was changed (24 hours)


# Define a helper function to read from payload
def _safe_get (payload: Dict [str, Any], key: str, default = None):
    if not isinstance(payload, dict):
        return default
    return payload.get(key, default)

# Create function to fetch events from the db for an account within LOOKBACK_DAYS, using created_at as basis
def fetch_recent_events(db: Session, account_id: str) -> List[Event]:
    cutoff = datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)
    return (
        db.query(Event)
        .filter(Event.account_id == account_id)
        .filter(Event.created_at >= cutoff)
        .order_by(Event.created_at.asc())
        .all()
    )

# Function to build all the signals and return a dictionary format for the API
def build_signals(db: Session, account_id: str) -> List[Dict[str, Any]]:
    events = fetch_recent_events(db, account_id)

    # Track known devices and counterparties seen hostorically (within Lookback period of 30 days)
    known_devices: Set[str] = set()
    known_counterparties: Set[str] = set()

    # Track when profile was last changed
    most_recent_profile_change: Tuple[datetime | None, int | None] = (None, None)

    signals: List[Dict[str, Any]] = []

    for e in events:
        payload = e.payload or {}

        # -----DEVICE LOGIN SIGNALS-----
        if e.event_type == "device_login":
            device_id = _safe_get(payload, "device_id")
            if device_id:
            # If device id is new and not in lookback window, send a signal
                if device_id not in known_devices:
                    signals.append({
                        "signal_name": "NEW_DEVICE_LOGIN",
                        "why_it_fired": f"Login from a new device id: '{device_id}' not seen in the last '{LOOKBACK_DAYS}'",
                        "evidence_event_ids": [e.id]                        
                    })
                    known_devices.add(device_id)  # Add it to known devices


        # -----PROFILE CHANGE SIGNALS-----
        if e.event_type == "profile_change":
            changed_fields = _safe_get(payload, "changed_fields", [])
            # Send signal for changed profile
            signals.append({
                "signal_name": "PROFILE_CHANGE",
                "why_it_fired": f"Profile change detected (fields: {changed_fields})",
                "evidence_event_ids": [e.id]                        
            })            
            most_recent_profile_change = (e.created_at, e.id) # Store it for later correlation


