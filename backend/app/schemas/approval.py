from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class ApprovalCreate(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected)$")
    comments: Optional[str] = None

class ApprovalResponse(BaseModel):
    id: int
    expense_id: int
    status: str
    reviewer_id: int
    comments: Optional[str] = None
    decided_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

