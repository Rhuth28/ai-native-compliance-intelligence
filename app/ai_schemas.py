"""
Create structured output so the AI always returns clear responses text
"""

from pydantic import BaseModel, Field
from typing import List, Literal


WorkflowPath = Literal["MONITOR", "REQUEST_INFO", "REVIEW", "ESCALATE"]


class AIReasoningOut(BaseModel):
    narrative_summary: str
    known_facts: List[str]
    unknowns: List[str]

    workflow_path: WorkflowPath
    why_this_path: List[str]

    confidence: float = Field(ge=0.0, le=1.0)

    # the evidence must be concrete so that analysts can verify
    evidence_event_ids: List[int]

    # Policy citations from RAG retrieval which includes both source and chunk_id
    policy_citations: List[str]

    # safety boundary for the AI
    ai_stop: str