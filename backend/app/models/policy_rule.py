from sqlalchemy import Column, Integer, String, Numeric, Boolean, Text, DateTime
from sqlalchemy.sql import func
from backend.app.core.database import Base

class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String, nullable=False)
    threshold_value = Column(Numeric(10, 2), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), onupdate=func.current_timestamp(), nullable=True)