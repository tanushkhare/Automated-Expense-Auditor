from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

class UserBase(BaseModel):
    email: str
    full_name: str
    role: Optional[str] = "employee"
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ExpenseBase(BaseModel):
    merchant: str
    amount: Decimal
    currency: Optional[str] = "USD"
    category: Optional[str] = "General"
    description: Optional[str] = None
    expense_date: Optional[datetime] = None
    status: Optional[str] = "draft"

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    merchant: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    expense_date: Optional[datetime] = None
    status: Optional[str] = None

class ReceiptResponse(BaseModel):
    id: int
    expense_id: int
    file_path: str
    content_type: str
    file_size: int
    upload_status: Optional[str] = "uploaded"
    ocr_status: Optional[str] = "pending"
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ExpenseResponse(ExpenseBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    receipt: Optional[ReceiptResponse] = None

    model_config = ConfigDict(from_attributes=True)

