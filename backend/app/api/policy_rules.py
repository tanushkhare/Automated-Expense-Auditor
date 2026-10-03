from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.policy_rule import PolicyRuleCreate, PolicyRuleUpdate, PolicyRuleResponse
from backend.app.services import policy_rule_service

router = APIRouter(prefix="/policy-rules", tags=["Policy Rules"])

@router.post("/", response_model=PolicyRuleResponse, status_code=status.HTTP_201_CREATED)
def create_policy_rule(rule: PolicyRuleCreate, db: Session = Depends(get_db)):
    return policy_rule_service.create_policy_rule(db=db, rule=rule)

@router.get("/", response_model=List[PolicyRuleResponse])
def read_policy_rules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return policy_rule_service.get_policy_rules(db=db, skip=skip, limit=limit)

@router.get("/{rule_id}", response_model=PolicyRuleResponse)
def read_policy_rule(rule_id: int, db: Session = Depends(get_db)):
    return policy_rule_service.get_policy_rule(db=db, rule_id=rule_id)

@router.put("/{rule_id}", response_model=PolicyRuleResponse)
def update_policy_rule(rule_id: int, rule_update: PolicyRuleUpdate, db: Session = Depends(get_db)):
    return policy_rule_service.update_policy_rule(db=db, rule_id=rule_id, rule_update=rule_update)

@router.delete("/{rule_id}", response_model=PolicyRuleResponse)
def delete_policy_rule(rule_id: int, db: Session = Depends(get_db)):
    return policy_rule_service.delete_policy_rule(db=db, rule_id=rule_id)
