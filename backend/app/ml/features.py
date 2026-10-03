import numpy as np
from decimal import Decimal
from datetime import datetime

class ExpenseFeatureExtractor:
    """
    Deterministic feature extractor mapping Expense objects to numerical vectors
    for Isolation Forest unsupervised anomaly detection.
    """
    def __init__(self):
        pass

    def extract_features(self, expense) -> list:
        amount_val = float(expense.amount) if expense.amount is not None else 0.0

        if expense.expense_date:
            dt = expense.expense_date
            day_of_week = float(dt.weekday())
            hour = float(dt.hour)
            day = float(dt.day)
            month = float(dt.month)
        else:
            day_of_week = 0.0
            hour = 12.0
            day = 1.0
            month = 1.0

        category_hash = float(abs(hash(expense.category or "General")) % 1000) / 1000.0
        merchant_hash = float(abs(hash(expense.merchant or "Unknown")) % 1000) / 1000.0

        return [
            amount_val,
            day_of_week,
            hour,
            day,
            month,
            category_hash,
            merchant_hash
        ]

    def transform_batch(self, expenses) -> np.ndarray:
        if not expenses:
            return np.array([]).reshape(0, 7)
        feature_matrix = [self.extract_features(e) for e in expenses]
        return np.array(feature_matrix, dtype=float)
