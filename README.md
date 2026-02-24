# AI-Native Compliance Intelligence Engine

## Overview
Prototype compliance engine that ingests financial events and stores them for behavioral risk analysis.

It replaces alerts, and
proactively monitors account activities, aggregates behavioral signals, produces a risk narrative and recommends actions with confidence score

The human in the loop:
Approves escalation, freeze accounts if necessary, files regulatory reports and overrides unclear cases

What breaks first at scale:
From the AI:
False positive amplification, model drift, and accumulated bias

## Tech Stack
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic

## Setup
1. Create virtual environment
2. pip install -r requirements.txt
3. uvicorn app.main:app --reload

## Current Features
- Event ingestion endpoint
- SQLite persistence

