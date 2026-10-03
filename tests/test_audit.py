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
from backend.app.models.audit_result import AuditResult
from backend.app.models.receipt import Receipt
from backend.app.models.expense import Expense
from backend.app.models.user import User
from backend.app.models.policy_rule import PolicyRule

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
    
    db = TestingSessionLocal()
    try:
        db.query(AuditResult).delete()
        db.query(Receipt).delete()
        db.query(Expense).delete()
        db.query(User).delete()
        db.query(PolicyRule).delete()
        db.commit()
    finally:
        db.close()

def create_test_user_and_expense(amount=100.00):
    unique_suffix = int(time.time() * 1000000)
    user_res = client.post("/api/v1/users/", json={
        "email": f"user_{unique_suffix}@enterprise.com",
        "full_name": "Audit Test User",
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

def test_audit_expense_no_active_rules():
    expense_id = create_test_user_and_expense(150.00)
    response = client.post(f"/api/v1/expenses/{expense_id}/audit")
    assert response.status_code == 201
    data = response.json()
    assert data["passed"] is True
    assert data["expense_id"] == expense_id

def test_audit_expense_amount_rule_pass():
    client.post("/api/v1/policy-rules/", json={
        "name": "Audit Max Amount Pass",
        "rule_type": "max_amount",
        "threshold_value": 500.0,
        "is_active": True
    })

    expense_id = create_test_user_and_expense(200.00)
    response = client.post(f"/api/v1/expenses/{expense_id}/audit")
    assert response.status_code == 201
    assert response.json()["passed"] is True

def test_audit_expense_amount_rule_violation():
    client.post("/api/v1/policy-rules/", json={
        "name": "Audit Max Amount Violate",
        "rule_type": "max_amount",
        "threshold_value": 100.0,
        "is_active": True
    })

    expense_id = create_test_user_and_expense(250.00)
    response = client.post(f"/api/v1/expenses/{expense_id}/audit")
    assert response.status_code == 201
    data = response.json()
    assert data["passed"] is False
    assert "Audit Max Amount Violate" in data["flags"]

def test_audit_expense_receipt_required_missing():
    client.post("/api/v1/policy-rules/", json={
        "name": "Receipt Required Rule",
        "rule_type": "receipt_required",
        "threshold_value": None,
        "is_active": True
    })

    expense_id = create_test_user_and_expense(50.00)
    response = client.post(f"/api/v1/expenses/{expense_id}/audit")
    assert response.status_code == 201
    data = response.json()
    assert data["passed"] is False
    assert "Receipt Required Rule" in data["flags"]

def test_audit_expense_receipt_required_present():
    client.post("/api/v1/policy-rules/", json={
        "name": "Receipt Required Present Rule",
        "rule_type": "receipt_required",
        "threshold_value": None,
        "is_active": True
    })

    expense_id = create_test_user_and_expense(50.00)
    client.post(
        f"/api/v1/expenses/{expense_id}/receipt",
        files={"file": ("receipt.jpg", io.BytesIO(b"receipt bytes"), "image/jpeg")}
    )

    response = client.post(f"/api/v1/expenses/{expense_id}/audit")
    assert response.status_code == 201
    data = response.json()
    assert data["passed"] is True

def test_audit_expense_multiple_rules_violations():
    client.post("/api/v1/policy-rules/", json={
        "name": "Multi Rule Amount",
        "rule_type": "max_amount",
        "threshold_value": 50.0,
        "is_active": True
    })
    client.post("/api/v1/policy-rules/", json={
        "name": "Multi Rule Receipt",
        "rule_type": "receipt_required",
        "threshold_value": None,
        "is_active": True
    })

    expense_id = create_test_user_and_expense(150.00)
    response = client.post(f"/api/v1/expenses/{expense_id}/audit")
    assert response.status_code == 201
    data = response.json()
    assert data["passed"] is False
    assert "Multi Rule Amount" in data["flags"]
    assert "Multi Rule Receipt" in data["flags"]

def test_audit_expense_not_found():
    response = client.post("/api/v1/expenses/99999/audit")
    assert response.status_code == 404

def test_re_audit_updates_existing_result():
    client.post("/api/v1/policy-rules/", json={
        "name": "Reaudit Rule",
        "rule_type": "max_amount",
        "threshold_value": 100.0,
        "is_active": True
    })

    expense_id = create_test_user_and_expense(50.00)
    res1 = client.post(f"/api/v1/expenses/{expense_id}/audit")
    id1 = res1.json()["id"]
    assert res1.json()["passed"] is True

    client.put(f"/api/v1/expenses/{expense_id}", json={"amount": 200.00})

    res2 = client.post(f"/api/v1/expenses/{expense_id}/audit")
    id2 = res2.json()["id"]
    assert id1 == id2
    assert res2.json()["passed"] is False

def test_inactive_rules_ignored():
    client.post("/api/v1/policy-rules/", json={
        "name": "Inactive Rule",
        "rule_type": "max_amount",
        "threshold_value": 10.0,
        "is_active": False
    })

    expense_id = create_test_user_and_expense(500.00)
    response = client.post(f"/api/v1/expenses/{expense_id}/audit")
    assert response.status_code == 201
    assert response.json()["passed"] is True

def test_get_audit_result():
    expense_id = create_test_user_and_expense(50.00)
    client.post(f"/api/v1/expenses/{expense_id}/audit")

    response = client.get(f"/api/v1/expenses/{expense_id}/audit")
    assert response.status_code == 200
    assert response.json()["expense_id"] == expense_id

def test_get_audit_result_not_found():
    expense_id = create_test_user_and_expense(50.00)
    response = client.get(f"/api/v1/expenses/{expense_id}/audit")
    assert response.status_code == 404
