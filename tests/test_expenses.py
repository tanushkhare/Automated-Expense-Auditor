import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.core.database import Base, get_db

# Use an in-memory SQLite database for testing
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

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "Automated Expense Auditor API"}

def test_register_user_and_create_expense():
    # 1. Register a new user
    user_response = client.post(
        "/api/v1/users/",
        json={
            "email": "auditor.test@enterprise.com",
            "full_name": "Test Auditor",
            "is_active": True,
            "password": "SecurePassword123"
        }
    )
    assert user_response.status_code == 201
    user_data = user_response.json()
    assert user_data["email"] == "auditor.test@enterprise.com"
    user_id = user_data["id"]

    # 2. Create an expense for this user
    expense_response = client.post(
        f"/api/v1/users/{user_id}/expenses/",
        json={
            "merchant": "Enterprise Airlines",
            "amount": 450.75,
            "currency": "USD",
            "category": "Travel",
            "description": "Flight to client meeting",
            "status": "draft"
        }
    )
    assert expense_response.status_code == 201
    expense_data = expense_response.json()
    assert expense_data["merchant"] == "Enterprise Airlines"
    assert float(expense_data["amount"]) == 450.75
    assert expense_data["user_id"] == user_id
    expense_id = expense_data["id"]

    # 3. Read the expense back
    get_expense_response = client.get(f"/api/v1/expenses/{expense_id}")
    assert get_expense_response.status_code == 200
    assert get_expense_response.json()["merchant"] == "Enterprise Airlines"

    # 4. List expenses
    list_response = client.get("/api/v1/expenses/")
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1
