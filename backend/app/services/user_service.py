from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.schemas.expense import UserCreate
from backend.app.core.security import get_password_hash
from fastapi import HTTPException, status

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

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
