import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.expense import Expense
from backend.app.models.audit_result import AuditResult
from backend.app.models.anomaly_score import AnomalyScore
from backend.app.ml.anomaly_detector import IsolationForestDetector

# Initialize singleton/reusable detector instance
_ml_detector = None

def get_ml_detector():
    global _ml_detector
    if _ml_detector is None:
        _ml_detector = IsolationForestDetector()
    return _ml_detector

def scan_expense_for_anomalies(db: Session, expense_id: int) -> AnomalyScore:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found."
        )

    audit_result = db.query(AuditResult).filter(AuditResult.expense_id == expense_id).first()
    if not audit_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expense must be audited before running anomaly scan."
        )

    heuristic_score = 0.0
    details_list = []

    # 1. Audit Failure check (+40 points)
    if not audit_result.passed:
        heuristic_score += 40.0
        details_list.append({"signal": "audit_failed", "points": 40.0, "message": "Expense failed policy audit compliance."})

    # 2. Parse violations from audit flags
    violations = []
    if audit_result.flags:
        try:
            violations = json.loads(audit_result.flags)
        except Exception:
            violations = []

    violation_points = len(violations) * 15.0
    if violation_points > 0:
        heuristic_score += violation_points
        details_list.append({
            "signal": "policy_violations",
            "points": violation_points,
            "message": f"Found {len(violations)} policy violation(s)."
        })

    has_receipt_violation = any(v.get("rule_type") == "receipt_required" for v in violations)
    if has_receipt_violation:
        heuristic_score += 15.0
        details_list.append({"signal": "missing_receipt_violation", "points": 15.0, "message": "Mandatory receipt is missing."})

    # 3. High expense amount check (> $1,000.00 adds +20 points)
    exp_amount = float(expense.amount) if expense.amount is not None else 0.0
    if exp_amount > 1000.0:
        heuristic_score += 20.0
        details_list.append({
            "signal": "high_amount",
            "points": 20.0,
            "message": f"Expense amount {exp_amount} exceeds high-value threshold ($1,000.00)."
        })

    heuristic_score = max(0.0, min(100.0, heuristic_score))

    # --- ML Isolation Forest Integration ---
    detector = get_ml_detector()
    ml_available = detector.is_available()
    ml_score_raw = 0.0
    ml_scaled = 0.0
    fallback_used = not ml_available

    if ml_available:
        try:
            ml_score_raw = detector.score(expense) # returns [0.0, 1.0]
            ml_scaled = ml_score_raw * 100.0
        except Exception as e:
            fallback_used = True
            ml_score_raw = 0.0
            ml_scaled = 0.0

    # Hybrid Combination Formula: 60% Heuristic, 40% ML (if available)
    if ml_available and not fallback_used:
        final_score = (heuristic_score * 0.60) + (ml_scaled * 0.40)
    else:
        final_score = heuristic_score

    final_score = max(0.0, min(100.0, final_score))

    if final_score <= 29.0:
        risk_level = "LOW"
    elif final_score <= 69.0:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    # Append hybrid breakdown into details list for transparency
    details_list.append({
        "signal": "hybrid_ml_scoring",
        "heuristic_score": round(heuristic_score, 2),
        "ml_score": round(ml_score_raw, 4),
        "ml_scaled": round(ml_scaled, 2),
        "final_score": round(final_score, 2),
        "ml_available": ml_available,
        "fallback_used": fallback_used
    })

    evaluated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    details_json = json.dumps(details_list)

    anomaly_score = db.query(AnomalyScore).filter(AnomalyScore.expense_id == expense_id).first()
    if anomaly_score:
        anomaly_score.score = final_score
        anomaly_score.risk_level = risk_level
        anomaly_score.details = details_json
        anomaly_score.evaluated_at = evaluated_at
    else:
        anomaly_score = AnomalyScore(
            expense_id=expense_id,
            score=final_score,
            risk_level=risk_level,
            details=details_json,
            evaluated_at=evaluated_at
        )
        db.add(anomaly_score)

    db.commit()
    db.refresh(anomaly_score)
    return anomaly_score

def get_expense_anomaly_score(db: Session, expense_id: int) -> AnomalyScore:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found."
        )
    anomaly_score = db.query(AnomalyScore).filter(AnomalyScore.expense_id == expense_id).first()
    if not anomaly_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anomaly score not found for this expense."
        )
    return anomaly_score
