from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.receipt import Receipt
from backend.app.models.expense import Expense
from backend.app.services.ocr_providers.base import BaseOCRProvider
from backend.app.services.ocr_providers.mock_provider import MockOCRProvider

class OCRService:
    def __init__(self, provider: BaseOCRProvider = None):
        self.provider = provider or MockOCRProvider()

    def process_receipt_ocr(self, db: Session, expense_id: int) -> Receipt:
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found."
            )
        
        receipt = db.query(Receipt).filter(Receipt.expense_id == expense_id).first()
        if not receipt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found for this expense. Please upload a receipt first."
            )

        try:
            extracted_data = self.provider.extract_receipt_data(receipt.file_path)

            total_amount = extracted_data.get("total_amount")
            if total_amount is not None:
                if total_amount < 0:
                    raise ValueError("Extracted total amount cannot be negative.")
                receipt.total_amount = Decimal(str(total_amount))

            tax_amount = extracted_data.get("tax_amount")
            if tax_amount is not None:
                if tax_amount < 0:
                    raise ValueError("Extracted tax amount cannot be negative.")
                receipt.tax_amount = Decimal(str(tax_amount))

            receipt.merchant_name = extracted_data.get("merchant_name")
            receipt.transaction_date = extracted_data.get("transaction_date")
            receipt.currency = extracted_data.get("currency")
            receipt.receipt_number = extracted_data.get("receipt_number")
            receipt.raw_text = extracted_data.get("raw_text")
            receipt.confidence = extracted_data.get("confidence")
            receipt.ocr_status = "processed"

        except Exception as e:
            receipt.ocr_status = "failed"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"OCR processing failed: {str(e)}"
            )

        db.commit()
        db.refresh(receipt)
        return receipt

    def get_receipt_ocr_result(self, db: Session, expense_id: int) -> Receipt:
        receipt = db.query(Receipt).filter(Receipt.expense_id == expense_id).first()
        if not receipt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found for this expense."
            )
        if receipt.ocr_status == "pending":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OCR result not found. Receipt has not been processed yet."
            )
        return receipt
