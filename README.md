# AI-Native Compliance Intelligence Engine

## Overview
Prototype compliance engine that ingests financial events and stores them for behavioral risk analysis. It replaces alerts, and
proactively monitors account activities for some behavioural signals like large transactions, profile change and new login, produces a risk narrative, recommends actions with confidence score, intelligently routes the cases for review, actions with SLA provided for analysts.

### The human in the loop:
Approves escalation, freeze accounts where necessary, files regulatory reports and overrides unclear cases

### What breaks first at scale:
False positive amplification from the AI, model drift, policy changes, and accumulated bias

## Tech Stack
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic

## Setup
1. Create virtual environment
2. pip install -r requirements.txt
3. uvicorn app.main:app --reload
4. Install langchain and chroma db for RAG

## Current Features
- Event ingestion endpoint
- SQLite persistence
- Transaction signals
- Risk guardrails for risk assessment (deterministic)
- RAG for policy retrieval and citation for each created case
- Routing for each compiled case
- SLA for analysts


