from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class AuditResultResponse(BaseModel):
    id: int
    expense_id: int
    passed: bool
    flags: Optional[str] = None
    evaluated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

