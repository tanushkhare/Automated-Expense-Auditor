import os
import pytest
from unittest.mock import MagicMock
from backend.app.ml.train import train_isolation_forest, MIN_REQUIRED_RECORDS
from backend.app.models.expense import Expense
from decimal import Decimal

def test_train_insufficient_data():
    mock_session = MagicMock()
    mock_session.query().all.return_value = [
        Expense(id=1, amount=Decimal("10.0"), merchant="Test"),
        Expense(id=2, amount=Decimal("20.0"), merchant="Test2")
    ]
    result = train_isolation_forest(db_session=mock_session)
    assert result["status"] == "NOT_TRAINED_INSUFFICIENT_DATA"
    assert result["usable_records"] < MIN_REQUIRED_RECORDS
