from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuth:
    async def test_register_success(self, client: AsyncClient):
        response = await client.post("/auth/register", json={
            "email": "testuser@example.com",
            "password": "strongpassword"
        })
        assert response.status_code == 201
        assert "access_token" in response.json()

    async def test_register_duplicate_email(self, client: AsyncClient):
        await client.post("/auth/register", json={
            "email": "dupe@example.com",
            "password": "password"
        })
        response = await client.post("/auth/register", json={
            "email": "dupe@example.com",
            "password": "password"
        })
        assert response.status_code == 400
        assert response.json()["detail"] == "Пользователь уже существует"

    async def test_login_success(self, client: AsyncClient):
        email = "loginuser@example.com"
        password = "mypassword"
        await client.post("/auth/register", json={"email": email, "password": password})
        response = await client.post("/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_login_wrong_password(self, client: AsyncClient):
        email = "wrongpass@example.com"
        await client.post("/auth/register", json={"email": email, "password": "correctpass"})
        response = await client.post("/auth/login", json={"email": email, "password": "wrongpass"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Неверный email или пароль"

    async def test_login_unknown_user(self, client: AsyncClient):
        response = await client.post("/auth/login", json={"email": "nonexistent@example.com", "password": "any"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Неверный email или пароль"
