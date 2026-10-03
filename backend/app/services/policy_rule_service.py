from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.policy_rule import PolicyRule
from backend.app.schemas.policy_rule import PolicyRuleCreate, PolicyRuleUpdate

def create_policy_rule(db: Session, rule: PolicyRuleCreate) -> PolicyRule:
    existing = db.query(PolicyRule).filter(PolicyRule.name == rule.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A policy rule with this name already exists."
        )
    db_rule = PolicyRule(
        name=rule.name,
        description=rule.description,
        rule_type=rule.rule_type,
        threshold_value=rule.threshold_value,
        is_active=rule.is_active
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

def get_policy_rules(db: Session, skip: int = 0, limit: int = 100) -> List[PolicyRule]:
    return db.query(PolicyRule).offset(skip).limit(limit).all()

def get_policy_rule(db: Session, rule_id: int) -> PolicyRule:
    db_rule = db.query(PolicyRule).filter(PolicyRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy rule not found."
        )
    return db_rule

def update_policy_rule(db: Session, rule_id: int, rule_update: PolicyRuleUpdate) -> PolicyRule:
    db_rule = get_policy_rule(db, rule_id)
    update_data = rule_update.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] != db_rule.name:
        existing = db.query(PolicyRule).filter(PolicyRule.name == update_data["name"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A policy rule with this name already exists."
            )

    for key, value in update_data.items():
        setattr(db_rule, key, value)

    db.commit()
    db.refresh(db_rule)
    return db_rule

def delete_policy_rule(db: Session, rule_id: int) -> PolicyRule:
    db_rule = get_policy_rule(db, rule_id)
    db.delete(db_rule)
    db.commit()
    return db_rule
