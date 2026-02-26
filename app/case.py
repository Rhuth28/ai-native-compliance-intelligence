"""
This builds an on-demand case that:
- Replace alerts with cohesive investigation-ready cases.
- Sums up timeline, signals, and risk into one structured object.
- Prepare clean input for AI reasoning
"""

# import dependencies
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from .models import Event
from .signals import build_signals
from .risk import assess_risk
from .signals import LOOKBACK_DAYS  # reuse LOOKBACK_DAYS constant of 30


# Define a function that retrives the events for the case builder
#For each account, using lookback window as logic, querying the db
def fetch_events_for_case(db: Session, account_id: str) -> List[Event]:   # fetch the event within the last lookback window
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)

    return(
        db.query(Event)
        .filter(Event.account_id == account_id)
        .order_by(Event.created_at.asc())
        .all()
    )


# Main case builder that returns a JSON of timeline, signals, risk assessment and some metadata
def build_case(db: Session, account_id: str) -> Dict[str, any]:
    events = fetch_events_for_case(db, account_id)
    signals = build_signals(db, account_id)
    risk = assess_risk(account_id=account_id, signals=signals)

    #Build clean timeline of events
    timeline = [{
        "event_id": e.id,
        "event_type": e.event_type,
        "created_at": e.created_at,
        "payload": e.payload,
        }
        for e in events
    ]

    #JSON case object
    case_object = {
        "case_id": f"CASE-{account_id}-{int(datetime.utcnow().timestamp())}",
        "account_id": account_id,
        "created_at": datetime.utcnow(),
        "timeline": timeline,
        "signals": signals,
        "risk_assessment": risk,
    }
    return case_object


