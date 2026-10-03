import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.core.database import Base, get_db

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

def test_create_policy_rule():
    response = client.post(
        "/api/v1/policy-rules/",
        json={
            "name": "Max Meal Limit",
            "description": "Meals cannot exceed 50 USD",
            "rule_type": "max_amount",
            "threshold_value": 50.0,
            "is_active": True
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Max Meal Limit"
    assert data["rule_type"] == "max_amount"
    assert data["threshold_value"] == 50.0
    assert data["is_active"] is True
    assert "id" in data

def test_create_duplicate_policy_rule_name():
    client.post(
        "/api/v1/policy-rules/",
        json={
            "name": "Unique Rule",
            "description": "Test unique name",
            "rule_type": "max_amount",
            "threshold_value": 100.0,
            "is_active": True
        }
    )
    response = client.post(
        "/api/v1/policy-rules/",
        json={
            "name": "Unique Rule",
            "description": "Duplicate test",
            "rule_type": "max_amount",
            "threshold_value": 200.0,
            "is_active": True
        }
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_get_policy_rules():
    client.post("/api/v1/policy-rules/", json={
        "name": "List Rule",
        "rule_type": "max_amount",
        "threshold_value": 20.0,
        "is_active": True
    })
    response = client.get("/api/v1/policy-rules/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1

def test_get_policy_rule_by_id():
    create_res = client.post(
        "/api/v1/policy-rules/",
        json={
            "name": "Fetch Rule",
            "description": "Fetch by ID test",
            "rule_type": "receipt_required",
            "threshold_value": None,
            "is_active": True
        }
    )
    rule_id = create_res.json()["id"]

    response = client.get(f"/api/v1/policy-rules/{rule_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Fetch Rule"

def test_get_policy_rule_not_found():
    response = client.get("/api/v1/policy-rules/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Policy rule not found."

def test_update_policy_rule():
    create_res = client.post(
        "/api/v1/policy-rules/",
        json={
            "name": "Old Rule Name",
            "description": "Will be updated",
            "rule_type": "max_amount",
            "threshold_value": 75.0,
            "is_active": True
        }
    )
    rule_id = create_res.json()["id"]

    response = client.put(
        f"/api/v1/policy-rules/{rule_id}",
        json={
            "name": "New Rule Name",
            "threshold_value": 85.0,
            "is_active": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Rule Name"
    assert data["threshold_value"] == 85.0
    assert data["is_active"] is False

def test_delete_policy_rule():
    create_res = client.post(
        "/api/v1/policy-rules/",
        json={
            "name": "Rule to Delete",
            "description": "Will be deleted",
            "rule_type": "max_amount",
            "threshold_value": 10.0,
            "is_active": True
        }
    )
    rule_id = create_res.json()["id"]

    response = client.delete(f"/api/v1/policy-rules/{rule_id}")
    assert response.status_code == 200

    get_res = client.get(f"/api/v1/policy-rules/{rule_id}")
    assert get_res.status_code == 404
