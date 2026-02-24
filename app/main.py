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