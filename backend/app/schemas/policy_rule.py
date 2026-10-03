from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class PolicyRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    rule_type: str = Field(..., min_length=1, max_length=100)
    threshold_value: Optional[float] = None
    is_active: bool = True

class PolicyRuleCreate(PolicyRuleBase):
    pass

class PolicyRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rule_type: Optional[str] = Field(None, min_length=1, max_length=100)
    threshold_value: Optional[float] = None
    is_active: Optional[bool] = None

class PolicyRuleResponse(PolicyRuleBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

