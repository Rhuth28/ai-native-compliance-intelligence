"""
Schemas for RAG output that will return top chunks + citations so the LLM can reference whatever policy used.
"""

from pydantic import BaseModel
from typing import List


class PolicySnippet(BaseModel):
    source: str      # policy file name
    chunk_id: int    # the chunk number within that file
    snippet: str     # chunk text


class PolicyContextOut(BaseModel):
    query: str
    top_k: int
    snippets: List[PolicySnippet]