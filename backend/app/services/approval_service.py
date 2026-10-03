from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.expense import Expense
from backend.app.models.approval import Approval
from backend.app.schemas.approval import ApprovalCreate

def decide_expense_approval(db: Session, expense_id: int, approval_in: ApprovalCreate, approver_id: int) -> Approval:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found."
        )

    decided_at = datetime.now(timezone.utc).replace(tzinfo=None)

    if approval_in.status == "approved":
        expense.status = "approved"
    elif approval_in.status == "rejected":
        expense.status = "rejected"

    approval = db.query(Approval).filter(Approval.expense_id == expense_id).first()
    if approval:
        approval.status = approval_in.status
        approval.approver_id = approver_id
        approval.comments = approval_in.comments
        approval.decided_at = decided_at
    else:
        approval = Approval()
        approval.expense_id = expense_id
        approval.status = approval_in.status
        approval.approver_id = approver_id
        approval.comments = approval_in.comments
        approval.decided_at = decided_at
        db.add(approval)

    db.commit()
    db.refresh(expense)
    db.refresh(approval)
    return approval

def get_expense_approval(db: Session, expense_id: int) -> Approval:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found."
        )
    approval = db.query(Approval).filter(Approval.expense_id == expense_id).first()
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval decision not found for this expense."
        )
    return approval
