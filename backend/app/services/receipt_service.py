import os
import shutil
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from backend.app.models.receipt import Receipt
from backend.app.models.expense import Expense

UPLOAD_DIR = "backend/uploads"

class ReceiptService:
    def __init__(self):
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    def save_and_process_receipt(self, db: Session, expense_id: int, file: UploadFile) -> Receipt:
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found."
            )

        allowed_types = ["image/jpeg", "image/png", "application/pdf"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only JPEG, PNG, and PDF are allowed."
            )

        contents = file.file.read()
        file_size = len(contents)
        MAX_SIZE = 5 * 1024 * 1024  # 5MB
        if file_size > MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds the maximum allowed size of 5MB."
            )

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        import uuid
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buffer:
            buffer.write(contents)

        existing_receipt = db.query(Receipt).filter(Receipt.expense_id == expense_id).first()
        if existing_receipt:
            if os.path.exists(existing_receipt.file_path):
                try:
                    os.remove(existing_receipt.file_path)
                except Exception:
                    pass
            db.delete(existing_receipt)
            db.commit()

        new_receipt = Receipt(
            expense_id=expense_id,
            file_path=file_path,
            content_type=file.content_type,
            file_size=file_size,
            upload_status="uploaded",
            ocr_status="pending"
        )

        db.add(new_receipt)
        db.commit()
        db.refresh(new_receipt)
        return new_receipt

receipt_service = ReceiptService()

def save_and_process_receipt(db: Session, expense_id: int, file: UploadFile) -> Receipt:
    return receipt_service.save_and_process_receipt(db=db, expense_id=expense_id, file=file)
