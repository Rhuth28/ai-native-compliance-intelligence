"""
AI Decision Layer for AI Reasoning + Workflow Path Selection
It uses case object and Policy snippets and Outputs:
- A strict JSON structure with Pydantic validations
- Includes workflow_path: MONITOR | REQUEST_INFO | REVIEW | ESCALATE
- Includes evidence_event_ids + policy_citations
- Includes explicit "AI STOP" boundary
"""


#Import dependencies
import json
from typing import Dict, Any, List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import ValidationError

from .ai_schemas import AIReasoningOut

load_dotenv()


# Convert RAG results to a citation list
def _build_policy_citations(policy_snippets: List[Dict[str, Any]]) -> List[str]:
    citations = []
    for s in policy_snippets:
        citations.append(f"{s.get('source', 'unknown')}#chunk_{s.get('chunk_id', -1)}")  #traceable policy reference-grounded reasoning
    return citations


# Create helper that builds structured JSON payload for the model
def _build_prompt_payload(case_obj: Dict[str, Any], policy_snippets: List[Dict[str, Any]]) -> Dict[str, Any]:
    risk = case_obj.get("risk_assessment", {})
    timeline = case_obj.get("timeline", [])

    # create compact timeline that takes in all necessary fields
    compact_timeline = [
        {
            "event_id": e.get("event_id"),
            "event_type": e.get("event_type"),
            "created_at": str(e.get("created_at")),
            "payload": e.get("payload", {}),
        }
        for e in timeline[-20:]  # checks the last 20 events
    ]

    return {
        "account_id": case_obj.get("account_id"),
        "risk_band": risk.get("risk_band"),
        "risk_score": risk.get("risk_score"),
        "fired_signals": risk.get("fired_signals", []),
        "signal_breakdown": risk.get("score_breakdown", {}),
        "timeline": compact_timeline,
        "policy_snippets": policy_snippets,  # includes source/chunk_id/snippet
    }


# Call the LLM and return a validated structured JSON output
def generate_ai_reasoning(case_obj: Dict[str, Any], policy_snippets: List[Dict[str, Any]]) -> Dict[str, Any]:
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)  #temperature of 0 ensures the result is factual

    citations = _build_policy_citations(policy_snippets)
    payload = _build_prompt_payload(case_obj, policy_snippets)

    system = SystemMessage(content=(
        "You are a compliance decision support assistant.\n"
        "You must return ONLY valid JSON.\n"
        "Your job is to summarize the case, identify unknowns, and choose a workflow path.\n\n"
        "Allowed workflow_path values: MONITOR, REQUEST_INFO, REVIEW, ESCALATE.\n"
        "IMPORTANT SAFETY RULES:\n"
        "- You MUST include an 'ai_stop' string stating that AI cannot freeze/restrict accounts or file regulatory reports.\n"
        "- Every claim must be supported by evidence_event_ids.\n"
        "- You must include policy_citations using the provided policy snippets.\n"
        "- If uncertain, choose REVIEW.\n"
    ))

    # The returned JSON must match AIReasoningOut so that the output remains consistent and easy to validate.
    human = HumanMessage(content=(
        "Return a JSON object with exactly these keys:\n"
        "{\n"
        '  "narrative_summary": string,\n'
        '  "known_facts": [string, ...],\n'
        '  "unknowns": [string, ...],\n'
        '  "workflow_path": "MONITOR|REQUEST_INFO|REVIEW|ESCALATE",\n'
        '  "why_this_path": [string, ...],\n'
        '  "confidence": number between 0 and 1,\n'
        '  "evidence_event_ids": [int, ...],\n'
        '  "policy_citations": [string, ...],\n'
        '  "ai_stop": string\n'
        "}\n\n"
        "Here is the case payload (JSON):\n"
        f"{json.dumps(payload, ensure_ascii=False)}\n\n"
        "Policy citation format must be like: source.md#chunk_12\n"
        f"Available citations: {citations}\n"
        "Only use citations from the available list.\n"
        "Return ONLY JSON. No markdown.\n"
    ))

    raw = model.invoke([system, human]).content

    # Parse the JSON
    try:
        data = json.loads(raw)
    except Exception:
        # Fail safe: if model output isn't valid JSON, force REVIEW
        return AIReasoningOut(
            narrative_summary="Model output could not be parsed. Failing safe to human review.",
            known_facts=[],
            unknowns=["Model returned invalid JSON."],
            workflow_path="REVIEW",
            why_this_path=["Fail-safe: invalid model output."],
            confidence=0.0,
            evidence_event_ids=[],
            policy_citations=citations[:1] if citations else [],
            ai_stop="AI cannot freeze/restrict accounts or file regulatory reports. Human must decide enforcement."
        ).model_dump()

    # Validate against schema
    try:
        validated = AIReasoningOut(**data)
        return validated.model_dump()
    except ValidationError:
        # Fail safe: if schema validation fails, force REVIEW
        return AIReasoningOut(
            narrative_summary="Model output failed schema validation. Failing safe to human review.",
            known_facts=[],
            unknowns=["Model output did not match required schema."],
            workflow_path="REVIEW",
            why_this_path=["Fail-safe: schema validation failed."],
            confidence=0.0,
            evidence_event_ids=[],
            policy_citations=citations[:1] if citations else [],
            ai_stop="AI cannot freeze/restrict accounts or file regulatory reports. Human must decide enforcement."
        ).model_dump()