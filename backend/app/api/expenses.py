from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user, require_role, oauth2_scheme
from backend.app.models.expense import Expense
from backend.app.models.user import User
from backend.app.schemas.expense import (
    UserCreate, UserResponse,
    ExpenseCreate, ExpenseUpdate, ExpenseResponse,
    ReceiptResponse
)
from backend.app.schemas.audit import AuditResultResponse
from backend.app.schemas.anomaly import AnomalyScoreResponse
from backend.app.schemas.approval import ApprovalCreate, ApprovalResponse
from backend.app.schemas.ocr import OCRResponse
from backend.app.services import expense_service, receipt_service, audit_service, anomaly_service, approval_service
from backend.app.services.ocr_service import OCRService

router = APIRouter(tags=["Automated Expense Auditor"])

@router.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = expense_service.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return expense_service.create_user(db=db, user=user)

@router.post("/users/{user_id}/expenses/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense_for_user(
    user_id: int, 
    expense: ExpenseCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user and current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to create expenses for other users.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return expense_service.create_expense(db=db, expense=expense, user_id=user_id)

@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def read_expense(
    expense_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_expense = expense_service.get_expense(db, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if current_user and current_user.role == "employee" and db_expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this expense.")
    return db_expense

@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int, 
    expense_update: ExpenseUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_expense = expense_service.get_expense(db, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if current_user and current_user.role == "employee" and db_expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this expense.")
    return expense_service.update_expense(db, expense_id=expense_id, expense_update=expense_update)

@router.delete("/expenses/{expense_id}", response_model=ExpenseResponse)
def delete_expense(
    expense_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_expense = expense_service.get_expense(db, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if current_user and current_user.role == "employee" and db_expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this expense.")
    return expense_service.delete_expense(db, expense_id=expense_id)

@router.post("/expenses/{expense_id}/receipt", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
def upload_expense_receipt(
    expense_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_expense = expense_service.get_expense(db, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if current_user and current_user.role == "employee" and db_expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to upload receipts for this expense.")
    return receipt_service.save_and_process_receipt(db=db, expense_id=expense_id, file=file)

@router.post("/expenses/{expense_id}/audit", response_model=AuditResultResponse, status_code=status.HTTP_201_CREATED)
def audit_expense_endpoint(
    expense_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_expense = expense_service.get_expense(db, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if current_user and current_user.role == "employee" and db_expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to audit this expense.")
    return audit_service.audit_expense(db=db, expense_id=expense_id)

@router.get("/expenses/{expense_id}/audit", response_model=AuditResultResponse)
def get_expense_audit_endpoint(
    expense_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_expense = expense_service.get_expense(db, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if current_user and current_user.role == "employee" and db_expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view audit results for this expense.")
    return audit_service.get_expense_audit(db=db, expense_id=expense_id)

@router.post("/expenses/{expense_id}/anomaly-scan", response_model=AnomalyScoreResponse, status_code=status.HTTP_201_CREATED)
def scan_expense_anomaly_endpoint(
    expense_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_expense = expense_service.get_expense(db, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if current_user and current_user.role == "employee" and db_expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to scan this expense.")
    return anomaly_service.scan_expense_for_anomalies(db=db, expense_id=expense_id)

@router.get("/expenses/{expense_id}/anomaly-score", response_model=AnomalyScoreResponse)
def get_expense_anomaly_score_endpoint(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_expense = expense_service.get_expense(db, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if current_user and current_user.role == "employee" and db_expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view anomaly score for this expense.")
    return anomaly_service.get_expense_anomaly_score(db=db, expense_id=expense_id)

@router.get("/expenses/", response_model=List[ExpenseResponse])
def read_expenses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user)
):
    if token and current_user and current_user.role == "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employees cannot access global expenses listing."
        )
    return db.query(Expense).offset(skip).limit(limit).all()

@router.post("/expenses/{expense_id}/approval", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED)
def decide_expense_approval_endpoint(
    expense_id: int, 
    approval_in: ApprovalCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    approver_id = current_user.id if current_user else 1
    return approval_service.decide_expense_approval(db=db, expense_id=expense_id, approval_in=approval_in, approver_id=approver_id)

@router.get("/expenses/{expense_id}/approval", response_model=ApprovalResponse)
def get_expense_approval_endpoint(
    expense_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return approval_service.get_expense_approval(db=db, expense_id=expense_id)

@router.post("/expenses/{expense_id}/ocr", response_model=OCRResponse, status_code=status.HTTP_201_CREATED)
def process_expense_ocr_endpoint(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_expense = expense_service.get_expense(db, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if current_user and current_user.role == "employee" and db_expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to process OCR for this expense.")
    
    ocr_service = OCRService()
    return ocr_service.process_receipt_ocr(db=db, expense_id=expense_id)

@router.get("/expenses/{expense_id}/ocr", response_model=OCRResponse)
def get_expense_ocr_endpoint(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_expense = expense_service.get_expense(db, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if current_user and current_user.role == "employee" and db_expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view OCR results for this expense.")
    
    ocr_service = OCRService()
    return ocr_service.get_receipt_ocr_result(db=db, expense_id=expense_id)
