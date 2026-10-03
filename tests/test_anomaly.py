import io
import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.services import receipt_service

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_env(tmp_path, monkeypatch):
    test_upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(receipt_service, "UPLOAD_DIR", test_upload_dir)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def create_test_user_and_expense(amount=100.00):
    unique_suffix = int(time.time() * 1000000)
    user_res = client.post("/api/v1/users/", json={
        "email": f"user_{unique_suffix}@enterprise.com",
        "full_name": "Anomaly Test User",
        "password": "Password123"
    })
    assert user_res.status_code == 201, user_res.text
    user_id = user_res.json()["id"]

    exp_res = client.post(f"/api/v1/users/{user_id}/expenses/", json={
        "merchant": "Test Merchant",
        "amount": amount,
        "currency": "USD",
        "category": "Travel"
    })
    assert exp_res.status_code == 201, exp_res.text
    return exp_res.json()["id"]

def test_anomaly_scan_clean_expense_low_risk():
    expense_id = create_test_user_and_expense(50.00)
    client.post(f"/api/v1/expenses/{expense_id}/audit")

    response = client.post(f"/api/v1/expenses/{expense_id}/anomaly-scan")
    assert response.status_code == 201
    data = response.json()
    assert data["risk_level"] == "LOW"
    assert data["score"] <= 29.0
    assert data["expense_id"] == expense_id

def test_anomaly_scan_failed_audit_elevated_risk():
    client.post("/api/v1/policy-rules/", json={
        "name": "Low Max Amount",
        "rule_type": "max_amount",
        "threshold_value": 40.0,
        "is_active": True
    })

    expense_id = create_test_user_and_expense(80.00)
    client.post(f"/api/v1/expenses/{expense_id}/audit")

    response = client.post(f"/api/v1/expenses/{expense_id}/anomaly-scan")
    assert response.status_code == 201
    data = response.json()
    assert data["score"] >= 40.0

def test_anomaly_scan_missing_receipt_risk():
    client.post("/api/v1/policy-rules/", json={
        "name": "Strict Receipt Rule",
        "rule_type": "receipt_required",
        "threshold_value": None,
        "is_active": True
    })

    expense_id = create_test_user_and_expense(50.00)
    client.post(f"/api/v1/expenses/{expense_id}/audit")

    response = client.post(f"/api/v1/expenses/{expense_id}/anomaly-scan")
    assert response.status_code == 201
    data = response.json()
    assert "missing_receipt_violation" in data["details"]

def test_anomaly_scan_high_amount_risk():
    expense_id = create_test_user_and_expense(1500.00)
    client.post(f"/api/v1/expenses/{expense_id}/audit")

    response = client.post(f"/api/v1/expenses/{expense_id}/anomaly-scan")
    assert response.status_code == 201
    data = response.json()
    assert "high_amount" in data["details"]

def test_anomaly_score_bounds_and_classification():
    expense_id = create_test_user_and_expense(5000.00)
    client.post(f"/api/v1/expenses/{expense_id}/audit")

    response = client.post(f"/api/v1/expenses/{expense_id}/anomaly-scan")
    assert response.status_code == 201
    score = response.json()["score"]
    risk = response.json()["risk_level"]
    assert 0.0 <= score <= 100.0
    if score <= 29.0:
        assert risk == "LOW"
    elif score <= 69.0:
        assert risk == "MEDIUM"
    else:
        assert risk == "HIGH"

def test_re_scan_updates_existing_anomaly_score():
    expense_id = create_test_user_and_expense(50.00)
    client.post(f"/api/v1/expenses/{expense_id}/audit")

    res1 = client.post(f"/api/v1/expenses/{expense_id}/anomaly-scan")
    id1 = res1.json()["id"]

    res2 = client.post(f"/api/v1/expenses/{expense_id}/anomaly-scan")
    id2 = res2.json()["id"]

    assert id1 == id2

def test_anomaly_scan_expense_not_found():
    response = client.post("/api/v1/expenses/99999/anomaly-scan")
    assert response.status_code == 404

def test_anomaly_scan_without_audit_fails():
    expense_id = create_test_user_and_expense(50.00)
    response = client.post(f"/api/v1/expenses/{expense_id}/anomaly-scan")
    assert response.status_code == 400

def test_get_anomaly_score_success_and_not_found():
    expense_id = create_test_user_and_expense(50.00)
    
    get_res = client.get(f"/api/v1/expenses/{expense_id}/anomaly-score")
    assert get_res.status_code == 404

    client.post(f"/api/v1/expenses/{expense_id}/audit")
    client.post(f"/api/v1/expenses/{expense_id}/anomaly-scan")

    get_res2 = client.get(f"/api/v1/expenses/{expense_id}/anomaly-score")
    assert get_res2.status_code == 200
    assert get_res2.json()["expense_id"] == expense_id
