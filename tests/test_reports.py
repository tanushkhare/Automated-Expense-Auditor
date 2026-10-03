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

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_create_and_read_report():
    # Create report
    response = client.post(
        "/api/v1/reports/",
        json={
            "title": "CRUD Test Report",
            "description": "Testing CRUD workflow",
            "content": "Detailed report content here...",
            "status": "draft"
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "CRUD Test Report"
    assert "id" in data
    report_id = data["id"]

    # Read single report
    response_get = client.get(f"/api/v1/reports/{report_id}")
    assert response_get.status_code == 200
    assert response_get.json()["id"] == report_id

def test_update_report():
    # Create report first
    response = client.post(
        "/api/v1/reports/",
        json={
            "title": "Report to Update",
            "description": "Before update",
            "content": "Original content",
            "status": "draft"
        },
    )
    report_id = response.json()["id"]

    # Update report
    response_put = client.put(
        f"/api/v1/reports/{report_id}",
        json={
            "title": "Updated Technical Report",
            "status": "published"
        }
    )
    assert response_put.status_code == 200
    updated_data = response_put.json()
    assert updated_data["title"] == "Updated Technical Report"
    assert updated_data["status"] == "published"
    assert updated_data["description"] == "Before update" # unchanged field preserved

def test_delete_report():
    # Create report to delete
    response = client.post(
        "/api/v1/reports/",
        json={
            "title": "Report to Delete",
            "description": "Will be deleted",
            "content": "Content to delete",
            "status": "draft"
        },
    )
    report_id = response.json()["id"]

    # Delete report
    response_delete = client.delete(f"/api/v1/reports/{report_id}")
    assert response_delete.status_code == 200

    # Verify 404 after deletion
    response_get = client.get(f"/api/v1/reports/{report_id}")
    assert response_get.status_code == 404

def test_not_found_errors():
    # Test GET 404
    assert client.get("/api/v1/reports/99999").status_code == 404
    # Test PUT 404
    assert client.put("/api/v1/reports/99999", json={"title": "Non-existent"}).status_code == 404
    # Test DELETE 404
    assert client.delete("/api/v1/reports/99999").status_code == 404
