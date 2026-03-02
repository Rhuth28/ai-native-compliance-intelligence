# AI-Native Compliance Intelligence Engine

## Overview
A prototype compliance engine that ingests financial events and stores them for behavioral risk analysis. It replaces traditional, rule-based alerting with a full investigation-ready case pipeline: ingesting raw account events, extracting behavioural signals like large transactions, profile change and new login, scoring risk deterministically, retrieving relevant policy via RAG, and generating structured AI reasoning with an explicit workflow path recommendation with SLA.

Every AI decision is bounded by hard guardrails, grounded in evidence, and logged to a full audit trail.


## Architecture
Raw Events → Signal Extraction → Risk Scoring → Case Builder
                                                      ↓
                                             RAG Policy Retrieval
                                                      ↓
                                             AI Reasoning (LLM)
                                                      ↓
                                          Guardrails + Confidence Reconciliation
                                                      ↓
                                             Routing + SLA Assignment
                                                      ↓
                                             Audit Trail → Analyst Action


## How It Works
1. Event Intake
Raw financial events (device_login, profile_change, transaction_posted) are ingested and persisted. Each event stores a full JSON payload for traceability.

2. Signal Extraction
Events within a 30-day lookback window are scanned for behavioural signals:

NEW_DEVICE_LOGIN — login from a device not seen in 30 days
PROFILE_CHANGE — any change to account profile fields
LARGE_TRANSACTION — transaction ≥ CAD 3,000
NEW_PAYEE_LARGE_TRANSFER — first-ever transfer to a recipient above threshold
PROFILE_CHANGE_AND_TRANSFER_24HR — profile change followed by a transaction within 24 hours
Each signal includes evidence_event_ids so analysts can verify what triggered it.

3. Risk Scoring (Deterministic)
Signals are weighted and summed into a risk score with a band:

LOW: 0–39
MEDIUM: 40–69
HIGH: 70+
A deterministic confidence heuristic (based on score severity and signal count) is computed alongside the score.

4. Case Builder
Builds a structured, investigation-ready case object per account containing: full event timeline, fired signals, risk assessment, and metadata. Replaces manual alert triage.

5. RAG Policy Retrieval
Policy documents (.md / .txt) are chunked, embedded via OpenAI, and stored in a local Chroma vector DB. Relevant policy snippets are retrieved per case and passed to the AI with source + chunk citations.

6. AI Reasoning Layer
A GPT-4o-mini model receives the case payload and policy snippets and returns a structured JSON response including:

narrative_summary — plain-language case summary
known_facts / unknowns — what is and isn't established
workflow_path — one of MONITOR | REQUEST_INFO | REVIEW | ESCALATE
why_this_path — reasoning for the routing decision
confidence — AI self-assessed confidence (0–1)
evidence_event_ids — grounded references to specific events
policy_citations — traceable references to policy chunks
ai_stop — explicit statement that AI cannot freeze accounts or file regulatory reports

7. Guardrails + Confidence Reconciliation
Before routing, the system applies deterministic guardrails:
AI confidence below 0.65 → force REVIEW
Risk band HIGH + AI recommends MONITOR → force REVIEW
ESCALATE always requires human confirmation
Deterministic confidence and AI confidence are reconciled into a final_confidence (conservative minimum) with a confidence_gap surfaced to analysts.

8. SLA Assignment
Each routed case is assigned a deadline based on workflow path:

ESCALATE → 2 hours
REVIEW → 24 hours
REQUEST_INFO → 48 hours
MONITOR → no SLA
SLA status is computed as ON_TRACK, DUE_SOON, or BREACHED.

9. Audit Trail
Every AI routing decision is automatically logged to case_actions with full context: routed path, confidence scores, fired signals, policy citations, evidence IDs, and ai_stop. When an analyst acts (approve, override, escalate, request info), their decision is stored alongside the original AI context — building a feedback dataset for future model improvement.


## The human in the loop:
The system recommends. Humans decide.
Analysts are responsible for:
Approving or overriding AI routing
Freezing or restricting accounts
Filing regulatory reports (e.g. SARs)
Resolving ESCALATE cases

## What breaks first at scale:
- False positive amplification (compounding signals can over-score low-risk accounts)
- Model drift (AI reasoning quality degrades as policy or account behaviour patterns shift)

## Tech Stack
- FastAPI
- SQLAlchemy + SQLite (event and audit persistence)
- Pydantic (schema validation and structured output enforcement)
- LangChain + Chroma (RAG pipeline - policy chunking, embedding, retrieval)
- OpenAI — embeddings (text-embedding-3-small) and reasoning (gpt-4o-mini)

## Setup
1. Create and activate virtual environment
2. Install dependencies 
3. Add environment variables
4. Ingest policy documents
5. Start the server: uvicorn app.main:app --reload


## API Endpoints
1. GET/health (Service health check)
2. POST/events (Ingest a raw event)
3. GET/signals/{account_id} (Get behavioural signals for account)
4. GET/risk/{account_id} (Get risk score, band, and breakdown)
5. GET/case/{account_id} (Build full investigation-ready case)
6. GET/policy_context/{account_id} (Retrieve relevant policy snippets)
7. GET/ai_decision/{account_id} (Full AI reasoning + routing + SLA)
8. POST/cases/actions (Log analyst action on a case)


## Current Features
- Event ingestion endpoint
- SQLite persistence
- Transaction signals
- Risk guardrails for risk assessment (deterministic)
- RAG for policy retrieval and citation for each created case
- Routing for each compiled case
- SLA for analysts


