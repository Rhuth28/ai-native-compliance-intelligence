from pydantic import BaseModel
from typing import Optional, Dict, Any, Literal

ActionType = Literal["APPROVE", "OVERRIDE", "REQUEST_INFO", "ESCALATE"]

class ActionCreate(BaseModel):
    case_id: str
    account_id: str
    action: ActionType
    reason: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None