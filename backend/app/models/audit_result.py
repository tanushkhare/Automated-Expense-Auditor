from sqlalchemy import Column, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class AuditResult(Base):
    __tablename__ = "audit_results"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), unique=True, index=True, nullable=False)
    passed = Column(Boolean, nullable=False)
    flags = Column(Text, nullable=True)  # SQLite-compatible text/JSON string for rule violations
    evaluated_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())

    expense = relationship("Expense", back_populates="audit_result")