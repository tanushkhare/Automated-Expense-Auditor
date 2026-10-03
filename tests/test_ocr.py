import os
import io
import tempfile
import pytest
from fastapi import HTTPException
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.expense import Expense
from backend.app.models.receipt import Receipt
from backend.app.services.ocr_service import OCRService
from backend.app.services.ocr_providers.base import BaseOCRProvider
from backend.app.core.security import get_password_hash
from typing import Dict, Any

class FailingOCRProvider(BaseOCRProvider):
    def extract_receipt_data(self, file_path: str) -> Dict[str, Any]:
        raise RuntimeError("Simulated OCR provider cloud outage")

class MalformedOCRProvider(BaseOCRProvider):
    def extract_receipt_data(self, file_path: str) -> Dict[str, Any]:
        return {
            "merchant_name": "Bad Data Inc",
            "total_amount": -50.00,
            "confidence": 0.50
        }

class MockSuccessOCRProvider(BaseOCRProvider):
    def extract_receipt_data(self, file_path: str) -> Dict[str, Any]:
        return {
            "merchant_name": "Sample Enterprise Merchant",
            "transaction_date": None,
            "total_amount": 125.50,
            "tax_amount": 10.00,
            "currency": "USD",
            "receipt_number": "REC-998877",
            "raw_text": "SAMPLE ENTERPRISE MERCHANT",
            "confidence": 0.95
        }

def test_ocr_processing_success_unit():
    db = SessionLocal()
    try:
        user = User(email=f"u_{os.urandom(2).hex()}@enterprise.com", full_name="OCR Unit", hashed_password=get_password_hash("pass123"), role="employee")
        db.add(user)
        db.commit()
        db.refresh(user)

        expense = Expense(user_id=user.id, merchant="Test", amount=125.50, currency="USD", category="Travel", status="draft")
        db.add(expense)
        db.commit()
        db.refresh(expense)

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp_file.write(b"fake image")
        tmp_file.close()

        receipt = Receipt(
            expense_id=expense.id,
            file_path=tmp_file.name,
            content_type="image/jpeg",
            file_size=10,
            ocr_status="pending"
        )
        db.add(receipt)
        db.commit()

        service = OCRService(provider=MockSuccessOCRProvider())
        processed_receipt = service.process_receipt_ocr(db, expense.id)
        assert processed_receipt.ocr_status == "processed"
        assert processed_receipt.merchant_name == "Sample Enterprise Merchant"
        assert float(processed_receipt.total_amount) == 125.50

        result = service.get_receipt_ocr_result(db, expense.id)
        assert result.ocr_status == "processed"

        os.unlink(tmp_file.name)
    finally:
        db.close()

def test_ocr_provider_failure_unit():
    db = SessionLocal()
    try:
        user = User(email=f"u_{os.urandom(2).hex()}@enterprise.com", full_name="Fail OCR", hashed_password=get_password_hash("pass123"), role="employee")
        db.add(user)
        db.commit()
        db.refresh(user)

        expense = Expense(user_id=user.id, merchant="Test Fail", amount=50.00, status="draft")
        db.add(expense)
        db.commit()
        db.refresh(expense)

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp_file.write(b"fake image")
        tmp_file.close()

        receipt = Receipt(
            expense_id=expense.id,
            file_path=tmp_file.name,
            content_type="image/jpeg",
            file_size=10,
            ocr_status="pending"
        )
        db.add(receipt)
        db.commit()

        service = OCRService(provider=FailingOCRProvider())
        with pytest.raises(HTTPException) as exc_info:
            service.process_receipt_ocr(db, expense.id)
        assert exc_info.value.status_code == 422
        assert "OCR processing failed" in exc_info.value.detail

        db.refresh(receipt)
        assert receipt.ocr_status == "failed"
        os.unlink(tmp_file.name)
    finally:
        db.close()

def test_ocr_amount_validation_failure_unit():
    db = SessionLocal()
    try:
        user = User(email=f"u_{os.urandom(2).hex()}@enterprise.com", full_name="Malformed OCR", hashed_password=get_password_hash("pass123"), role="employee")
        db.add(user)
        db.commit()
        db.refresh(user)

        expense = Expense(user_id=user.id, merchant="Test Malformed", amount=50.00, status="draft")
        db.add(expense)
        db.commit()
        db.refresh(expense)

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp_file.write(b"fake image")
        tmp_file.close()

        receipt = Receipt(
            expense_id=expense.id,
            file_path=tmp_file.name,
            content_type="image/jpeg",
            file_size=10,
            ocr_status="pending"
        )
        db.add(receipt)
        db.commit()

        service = OCRService(provider=MalformedOCRProvider())
        with pytest.raises(HTTPException) as exc_info:
            service.process_receipt_ocr(db, expense.id)
        assert exc_info.value.status_code == 422
        assert "cannot be negative" in exc_info.value.detail

        os.unlink(tmp_file.name)
    finally:
        db.close()
