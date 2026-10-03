import os
from datetime import datetime, timezone
from typing import Dict, Any
from backend.app.services.ocr_providers.base import BaseOCRProvider

class MockOCRProvider(BaseOCRProvider):
    def extract_receipt_data(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise ValueError("Receipt file path does not exist for OCR processing.")
        
        return {
            "merchant_name": "Sample Enterprise Merchant",
            "transaction_date": datetime.now(timezone.utc).replace(tzinfo=None),
            "total_amount": 125.50,
            "tax_amount": 10.00,
            "currency": "USD",
            "receipt_number": "REC-998877",
            "raw_text": "SAMPLE ENTERPRISE MERCHANT\nDate: TODAY\nItems: Office Supplies\nTax: $10.00\nTotal: $125.50\nReceipt #: REC-998877",
            "confidence": 0.95
        }
