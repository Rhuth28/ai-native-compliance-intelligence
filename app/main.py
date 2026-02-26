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
from .rag import build_policy_query_from_case, retrieve_policy_snippets
from .rag_schemas import PolicyContextOut
from .ai_reasoning import generate_ai_reasoning
from .router import apply_guardrails
from .sla import assign_sla
from .actions import CaseAction
from .action_schemas import ActionCreate



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


#Retrieves RAG policies and return the policy snippets relevant to that case
@app.get("/policy_context/{account_id}", response_model=PolicyContextOut)
def get_policy_context(account_id: str, db: Session = Depends(get_db)):
    case_obj = build_case(db, account_id)
    query = build_policy_query_from_case(case_obj)
    snippets = retrieve_policy_snippets(query=query, top_k=3)

    return {"query": query, "top_k": 3, "snippets": snippets}



# Endpoint for ai decisioning
@app.get("/ai_decision/{account_id}")
def get_ai_decision(account_id: str, db: Session = Depends(get_db)):
    """
    This endpoint:
    - Builds case
    - Retrieves policy snippets (RAG)
    - Asks AI for structured reasoning + workflow path
    - Applies guardrails to produce a final routed path
    """
    case_obj = build_case(db, account_id)

    # retrieve the policy context
    query = build_policy_query_from_case(case_obj)
    policy_snippets = retrieve_policy_snippets(query=query, top_k=3)

    # AI reasoning
    ai_out = generate_ai_reasoning(case_obj=case_obj, policy_snippets=policy_snippets)

    # guardrails router
    risk_band = case_obj.get("risk_assessment", {}).get("risk_band", "UNKNOWN")
    routed = apply_guardrails(ai_out, risk_band=risk_band)
    # attach SLA to routed path
    case_created_at = case_obj.get("created_at")
    routed_path = routed.get("routed_path", "REVIEW")
    sla = assign_sla(created_at=case_created_at, routed_path=routed_path)

    return {
        "account_id": account_id,
        "query": query,
        "policy_snippets": policy_snippets,
        "ai_decision": routed,
        "sla": sla,
    }


#Endpoint for analyst action
@app.post("/cases/actions")
def log_case_action(payload: ActionCreate, db: Session = Depends(get_db)):
    # Simple guardrail---- overrides must have a reason
    if payload.action == "OVERRIDE" and not payload.reason:
        return {"error": "OVERRIDE requires a reason"}

    row = CaseAction(
        case_id=payload.case_id,
        account_id=payload.account_id,
        action=payload.action,
        reason=payload.reason,
        extra_data=payload.extra_data,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return {"message": "Action logged", "action_id": row.id}