"""
Main FastAPI application.
Implements the Event Intake Layer.
"""

# Import dependencies
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import engine, SessionLocal, Base
from .models import Event
from .schemas import EventCreate
from typing import List
from .signals import build_signals
from .signal_schemas import SignalOut
from .risk import assess_risk
from .risk_schemas import RiskOut
from .case import build_case


# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-Native Compliance Intelligence")

# Check the status of the site and ensure the service is running
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Dependency that gets DB session for every request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


#Receives all intake events
@app.post("/events")
def create_event(event: EventCreate, db: Session = Depends(get_db)):

    # Create new Event object
    new_event = Event(
        event_type=event.event_type,
        account_id=event.account_id,
        payload=event.payload,
    )

    # Store in database
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return {
        "message": "Event stored successfully",
        "event_id": new_event.id
    }

# Checks and computes all account signals based on recent events
@app.get("/signals/{account_id}", response_model=List[SignalOut])
def get_signals(account_id: str, db: Session = Depends(get_db)):
    return build_signals(db, account_id)


#Get risk for the account id - assign risk core + band
@app.get("/risk/{account_id}", response_model=RiskOut)
def get_risk(account_id: str, db: Session = Depends(get_db)):
    signals = build_signals(db, account_id)
    return assess_risk(account_id=account_id, signals=signals)


#Endpoint that builds a full-investigation ready case and replaces alerts
@app.get("/case/{account_id}")
def get_case(account_id: str, db: Session = Depends(get_db)):
    return build_case(db, account_id)