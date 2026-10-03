import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_successful_login_and_me():
    # Register user
    reg = client.post("/api/v1/users/", json={
        "email": "phase71.user@enterprise.com",
        "full_name": "Phase 71 User",
        "password": "SecurePassword123",
        "role": "employee",
        "is_active": True
    })
    assert reg.status_code == 201

    # Login
    login = client.post("/api/v1/auth/login", json={
        "email": "phase71.user@enterprise.com",
        "password": "SecurePassword123"
    })
    assert login.status_code == 200
    token_data = login.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # Test /users/me with token
    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    me_data = me.json()
    assert me_data["email"] == "phase71.user@enterprise.com"
    assert me_data["role"] == "employee"

def test_invalid_password_login():
    res = client.post("/api/v1/auth/login", json={
        "email": "phase71.user@enterprise.com",
        "password": "WrongPassword"
    })
    assert res.status_code == 401

def test_nonexistent_user_login():
    res = client.post("/api/v1/auth/login", json={
        "email": "nobody@enterprise.com",
        "password": "Password123"
    })
    assert res.status_code == 401

def test_users_me_without_auth():
    res = client.get("/api/v1/users/me")
    assert res.status_code == 401

def test_global_expenses_access_control():
    # 1. Create Employee
    client.post("/api/v1/users/", json={
        "email": "emp.test@enterprise.com",
        "full_name": "Employee Test",
        "password": "Password123",
        "role": "employee",
        "is_active": True
    })
    emp_login = client.post("/api/v1/auth/login", json={
        "email": "emp.test@enterprise.com",
        "password": "Password123"
    }).json()
    emp_token = emp_login["access_token"]

    # Employee tries to access global expenses -> 403 Forbidden
    emp_res = client.get("/api/v1/expenses/", headers={"Authorization": f"Bearer {emp_token}"})
    assert emp_res.status_code == 403

    # 2. Create Auditor
    client.post("/api/v1/users/", json={
        "email": "auditor.test@enterprise.com",
        "full_name": "Auditor Test",
        "password": "Password123",
        "role": "auditor",
        "is_active": True
    })
    aud_login = client.post("/api/v1/auth/login", json={
        "email": "auditor.test@enterprise.com",
        "password": "Password123"
    }).json()
    aud_token = aud_login["access_token"]

    # Auditor tries to access global expenses -> 200 OK
    aud_res = client.get("/api/v1/expenses/", headers={"Authorization": f"Bearer {aud_token}"})
    assert aud_res.status_code == 200