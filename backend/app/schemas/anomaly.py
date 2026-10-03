from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class AnomalyScoreResponse(BaseModel):
    id: int
    expense_id: int
    score: float
    risk_level: str
    details: Optional[str] = None
    evaluated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

