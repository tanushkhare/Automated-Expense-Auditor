from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from backend.app.core.database import Base
from sqlalchemy.orm import relationship

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    approver_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    expense = relationship("Expense", back_populates="approvals", foreign_keys=[expense_id])

    @property
    def status(self) -> str:
        return self.action

    @status.setter
    def status(self, value: str):
        self.action = value

    @property
    def reviewer_id(self) -> int:
        return self.approver_id

    @reviewer_id.setter
    def reviewer_id(self, value: int):
        self.approver_id = value

    @property
    def decided_at(self) -> datetime:
        return self.created_at

    @decided_at.setter
    def decided_at(self, value: datetime):
        self.created_at = value
