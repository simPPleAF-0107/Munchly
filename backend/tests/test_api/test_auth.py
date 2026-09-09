import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_creates_user(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "Password123!",
        "name": "New User"
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_duplicate_email_returns_409(client: AsyncClient):
    # First registration
    await client.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "password": "Password123!",
        "name": "Dup User"
    })
    
    # Second registration with same email
    response = await client.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "password": "Password123!",
        "name": "Dup User"
    })
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_login_correct_credentials(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "password": "Password123!",
        "name": "Login User"
    })
    
    response = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "Password123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "wrong@example.com",
        "password": "Password123!",
        "name": "Wrong User"
    })
    
    response = await client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com",
        "password": "WrongPassword!"
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_me_returns_current_user(authenticated_client: AsyncClient):
    # authenticated_client fixture overrides get_current_user
    response = await authenticated_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_token_refresh(client: AsyncClient):
    reg_response = await client.post("/api/v1/auth/register", json={
        "email": "refresh@example.com",
        "password": "Password123!",
        "name": "Refresh User"
    })
    refresh_token = reg_response.json()["refresh_token"]
    
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
