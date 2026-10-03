from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ReportBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: str
    status: Optional[str] = "draft"

class ReportCreate(ReportBase):
    pass

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None

class ReportResponse(ReportBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
