from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class OCRResponse(BaseModel):
    id: int
    expense_id: int
    ocr_status: str
    merchant_name: Optional[str] = None
    transaction_date: Optional[datetime] = None
    total_amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    receipt_number: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

