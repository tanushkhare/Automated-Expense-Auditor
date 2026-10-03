from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.models.expense import Expense
from backend.app.schemas.expense import UserCreate, ExpenseCreate, ExpenseUpdate
from backend.app.core.security import get_password_hash
from fastapi import HTTPException, status

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def get_expense(db: Session, expense_id: int) -> Expense | None:
    return db.query(Expense).filter(Expense.id == expense_id).first()

def create_user(db: Session, user: UserCreate) -> User:
    existing_user = get_user_by_email(db, email=user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pass = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_pass,
        role=user.role if user.role else "employee",
        is_active=user.is_active if user.is_active is not None else True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_expense(db: Session, expense: ExpenseCreate, user_id: int) -> Expense:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    db_expense = Expense(
        user_id=user_id,
        merchant=expense.merchant,
        amount=expense.amount,
        currency=expense.currency or "USD",
        category=expense.category or "General",
        description=expense.description,
        expense_date=expense.expense_date,
        status=expense.status or "draft"
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

def update_expense(db: Session, expense_id: int, expense_update: ExpenseUpdate) -> Expense:
    db_expense = get_expense(db, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found.")
    
    update_data = expense_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_expense, key, value)
        
    db.commit()
    db.refresh(db_expense)
    return db_expense
