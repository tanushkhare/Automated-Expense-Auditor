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
        "full_name": "Approval Test User",
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

def test_approve_expense_success():
    expense_id = create_test_user_and_expense(150.00)
    response = client.post(f"/api/v1/expenses/{expense_id}/approval", json={
        "status": "approved",
        "reviewer_id": 1,
        "comments": "Looks good and compliant."
    })
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "approved"
    assert data["expense_id"] == expense_id
    assert data["reviewer_id"] == 1

def test_reject_expense_success():
    expense_id = create_test_user_and_expense(800.00)
    response = client.post(f"/api/v1/expenses/{expense_id}/approval", json={
        "status": "rejected",
        "reviewer_id": 2,
        "comments": "Exceeds standard business necessity."
    })
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "rejected"
    assert data["expense_id"] == expense_id

def test_approval_updates_existing_decision():
    expense_id = create_test_user_and_expense(200.00)
    
    res1 = client.post(f"/api/v1/expenses/{expense_id}/approval", json={
        "status": "rejected",
        "reviewer_id": 1,
        "comments": "Initial rejection."
    })
    id1 = res1.json()["id"]

    res2 = client.post(f"/api/v1/expenses/{expense_id}/approval", json={
        "status": "approved",
        "reviewer_id": 1,
        "comments": "Reconsidered and approved."
    })
    id2 = res2.json()["id"]

    assert id1 == id2
    assert res2.json()["status"] == "approved"

def test_approval_expense_not_found():
    response = client.post("/api/v1/expenses/99999/approval", json={
        "status": "approved",
        "reviewer_id": 1
    })
    assert response.status_code == 404

def test_get_approval_success_and_not_found():
    expense_id = create_test_user_and_expense(100.00)

    get_res = client.get(f"/api/v1/expenses/{expense_id}/approval")
    assert get_res.status_code == 404

    client.post(f"/api/v1/expenses/{expense_id}/approval", json={
        "status": "approved",
        "reviewer_id": 1
    })

    get_res2 = client.get(f"/api/v1/expenses/{expense_id}/approval")
    assert get_res2.status_code == 200
    assert get_res2.json()["expense_id"] == expense_id
