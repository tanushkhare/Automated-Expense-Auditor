from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    merchant = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD", nullable=False)
    category = Column(String, nullable=True)
    
    expense_date = Column(DateTime(timezone=True), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String, default="draft", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), onupdate=func.current_timestamp(), nullable=True)

    user = relationship("User", back_populates="expenses")
    receipt = relationship("Receipt", back_populates="expense", uselist=False, cascade="all, delete-orphan")
    audit_result = relationship("AuditResult", back_populates="expense", uselist=False, cascade="all, delete-orphan")
    anomaly_score = relationship("AnomalyScore", back_populates="expense", uselist=False, cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="expense", foreign_keys="Approval.expense_id", cascade="all, delete-orphan")