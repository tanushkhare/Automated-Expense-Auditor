from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), unique=True, index=True, nullable=False)
    file_path = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_status = Column(String, default="uploaded", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())

    ocr_status = Column(String, default="pending", nullable=False)
    merchant_name = Column(String, nullable=True)
    transaction_date = Column(DateTime(timezone=True), nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=True)
    tax_amount = Column(Numeric(10, 2), nullable=True)
    currency = Column(String, nullable=True)
    receipt_number = Column(String, nullable=True)
    raw_text = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)

    expense = relationship("Expense", back_populates="receipt")
