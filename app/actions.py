"""
Audit Trail that shows:
- Accountability (who decided what and when)
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON
from .database import Base

class CaseAction(Base):
    __tablename__ = "case_actions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, index=True)          # e.g., CASE-ACC123-...
    account_id = Column(String, index=True)
    action = Column(String)                       # APPROVE | OVERRIDE | REQUEST_INFO | ESCALATE
    reason = Column(String, nullable=True)        # reason for action, especially if it's OVERRIDE
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    extra_data = Column(JSON, nullable=True)        # e.g the previous routed_path