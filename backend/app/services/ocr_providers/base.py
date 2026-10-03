from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseOCRProvider(ABC):
    @abstractmethod
    def extract_receipt_data(self, file_path: str) -> Dict[str, Any]:
        pass
