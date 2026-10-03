from sqlalchemy import Column, Integer, Numeric, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class AnomalyScore(Base):
    __tablename__ = "anomaly_scores"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), unique=True, index=True, nullable=False)
    score = Column(Numeric(5, 4), nullable=False)
    risk_level = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    evaluated_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())

    expense = relationship("Expense", back_populates="anomaly_score")