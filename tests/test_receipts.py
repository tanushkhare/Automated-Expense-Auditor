import io
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
def setup_test_uploads(tmp_path, monkeypatch):
    # Redirect upload directory to a temporary directory during tests
    test_upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(receipt_service, "UPLOAD_DIR", test_upload_dir)

def test_upload_receipt_success():
    # 1. Create User and Expense
    user_res = client.post("/api/v1/users/", json={
        "email": "receipt.test@enterprise.com",
        "full_name": "Receipt Tester",
        "password": "Password123"
    })
    user_id = user_res.json()["id"]

    exp_res = client.post(f"/api/v1/users/{user_id}/expenses/", json={
        "merchant": "Office Depot",
        "amount": 75.50,
        "currency": "USD",
        "category": "Supplies"
    })
    expense_id = exp_res.json()["id"]

    # 2. Upload receipt file
    file_content = b"fake image receipt binary content"
    response = client.post(
        f"/api/v1/expenses/{expense_id}/receipt",
        files={"file": ("receipt.jpg", io.BytesIO(file_content), "image/jpeg")}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["expense_id"] == expense_id
    assert data["upload_status"] == "uploaded"
    assert "file_path" in data

def test_upload_receipt_expense_not_found():
    response = client.post(
        "/api/v1/expenses/99999/receipt",
        files={"file": ("receipt.jpg", io.BytesIO(b"content"), "image/jpeg")}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Expense not found"

def test_upload_receipt_invalid_type():
    user_res = client.post("/api/v1/users/", json={
        "email": "invalid.type@enterprise.com",
        "full_name": "Type Tester",
        "password": "Password123"
    })
    user_id = user_res.json()["id"]
    exp_res = client.post(f"/api/v1/users/{user_id}/expenses/", json={
        "merchant": "Bad File Corp",
        "amount": 10.00
    })
    expense_id = exp_res.json()["id"]

    response = client.post(
        f"/api/v1/expenses/{expense_id}/receipt",
        files={"file": ("malicious.exe", io.BytesIO(b"exe content"), "application/x-msdownload")}
    )
    assert response.status_code == 400

def test_upload_receipt_exceeds_size_limit():
    user_res = client.post("/api/v1/users/", json={
        "email": "size.test@enterprise.com",
        "full_name": "Size Tester",
        "password": "Password123"
    })
    user_id = user_res.json()["id"]
    exp_res = client.post(f"/api/v1/users/{user_id}/expenses/", json={
        "merchant": "Huge File Corp",
        "amount": 100.00
    })
    expense_id = exp_res.json()["id"]

    # Generate a file larger than 5MB
    large_content = b"0" * (5 * 1024 * 1024 + 1024)
    response = client.post(
        f"/api/v1/expenses/{expense_id}/receipt",
        files={"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}
    )
    assert response.status_code == 400
    assert "exceeds the maximum allowed size" in response.json()["detail"]

def test_replace_existing_receipt():
    user_res = client.post("/api/v1/users/", json={
        "email": "replace.test@enterprise.com",
        "full_name": "Replace Tester",
        "password": "Password123"
    })
    user_id = user_res.json()["id"]
    exp_res = client.post(f"/api/v1/users/{user_id}/expenses/", json={
        "merchant": "Restaurant",
        "amount": 50.00
    })
    expense_id = exp_res.json()["id"]

    # Upload first receipt
    res1 = client.post(
        f"/api/v1/expenses/{expense_id}/receipt",
        files={"file": ("receipt1.png", io.BytesIO(b"first receipt"), "image/png")}
    )
    assert res1.status_code == 201
    receipt_id_1 = res1.json()["id"]

    # Upload second receipt (replacement)
    res2 = client.post(
        f"/api/v1/expenses/{expense_id}/receipt",
        files={"file": ("receipt2.png", io.BytesIO(b"second replacement receipt"), "image/png")}
    )
    assert res2.status_code == 201
    receipt_id_2 = res2.json()["id"]

    # Should maintain the same receipt record ID but update file path
    assert receipt_id_1 == receipt_id_2