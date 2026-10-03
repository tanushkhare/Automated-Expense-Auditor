import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from backend.app.services.anomaly_service import scan_expense_for_anomalies
from backend.app.models.expense import Expense
from backend.app.models.audit_result import AuditResult
from backend.app.models.anomaly_score import AnomalyScore

def test_hybrid_anomaly_scoring_with_ml():
    mock_db = MagicMock()
    mock_expense = Expense(id=1, amount=Decimal("500.0"), category="Travel", merchant="Hotel")
    mock_audit = AuditResult(expense_id=1, passed=True, flags=None)
    
    mock_db.query().filter().first.side_effect = [mock_expense, mock_audit, None]

    with patch("backend.app.services.anomaly_service.get_ml_detector") as mock_get_det:
        mock_detector = MagicMock()
        mock_detector.is_available.return_value = True
        mock_detector.score.return_value = 0.5
        mock_get_det.return_value = mock_detector

        result = scan_expense_for_anomalies(mock_db, 1)
        assert result.score == 20.0 # heuristic 0.0 * 0.6 + 50.0 * 0.4 = 20.0
        assert result.risk_level == "LOW"

def test_hybrid_anomaly_fallback_when_ml_unavailable():
    mock_db = MagicMock()
    mock_expense = Expense(id=1, amount=Decimal("1500.0"), category="Travel", merchant="Hotel") # > 1000 adds 20 heuristic
    mock_audit = AuditResult(expense_id=1, passed=True, flags=None)
    
    mock_db.query().filter().first.side_effect = [mock_expense, mock_audit, None]

    with patch("backend.app.services.anomaly_service.get_ml_detector") as mock_get_det:
        mock_detector = MagicMock()
        mock_detector.is_available.return_value = False
        mock_get_det.return_value = mock_detector

        result = scan_expense_for_anomalies(mock_db, 1)
        assert result.score == 20.0 # Pure heuristic fallback
        assert result.risk_level == "LOW"
