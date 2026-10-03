import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.expense import Expense
from backend.app.models.policy_rule import PolicyRule
from backend.app.models.audit_result import AuditResult

def audit_expense(db: Session, expense_id: int) -> AuditResult:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found."
        )

    active_rules = db.query(PolicyRule).filter(PolicyRule.is_active == True).all()
    violations: List[Dict[str, Any]] = []

    for rule in active_rules:
        if rule.rule_type in ("max_amount", "amount_threshold"):
            if rule.threshold_value is not None:
                exp_amount = float(expense.amount) if expense.amount is not None else 0.0
                thresh_val = float(rule.threshold_value)
                if exp_amount > thresh_val:
                    violations.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "rule_type": rule.rule_type,
                        "message": f"Expense amount {exp_amount} exceeds maximum allowed threshold of {thresh_val}.",
                        "threshold": thresh_val,
                        "actual_value": exp_amount
                    })
        elif rule.rule_type == "receipt_required":
            has_receipt = expense.receipt is not None
            if not has_receipt:
                violations.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "rule_type": rule.rule_type,
                    "message": "Receipt is required for this expense but none was uploaded.",
                    "threshold": None,
                    "actual_value": None
                })
        elif rule.rule_type == "category_threshold":
            if rule.threshold_value is not None:
                exp_amount = float(expense.amount) if expense.amount is not None else 0.0
                thresh_val = float(rule.threshold_value)
                if exp_amount > thresh_val:
                    violations.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "rule_type": rule.rule_type,
                        "message": f"Expense amount {exp_amount} exceeds category threshold of {thresh_val}.",
                        "threshold": thresh_val,
                        "actual_value": exp_amount
                    })

    passed = len(violations) == 0
    flags_json = json.dumps(violations)
    evaluated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    if passed:
        expense.status = "compliant"
    else:
        expense.status = "flagged"

    audit_result = db.query(AuditResult).filter(AuditResult.expense_id == expense_id).first()
    if audit_result:
        audit_result.passed = passed
        audit_result.flags = flags_json
        audit_result.evaluated_at = evaluated_at
    else:
        audit_result = AuditResult(
            expense_id=expense_id,
            passed=passed,
            flags=flags_json,
            evaluated_at=evaluated_at
        )
        db.add(audit_result)

    db.commit()
    db.refresh(expense)
    db.refresh(audit_result)
    return audit_result

def get_expense_audit(db: Session, expense_id: int) -> AuditResult:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found."
        )
    audit_result = db.query(AuditResult).filter(AuditResult.expense_id == expense_id).first()
    if not audit_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit result not found for this expense."
        )
    return audit_result
