from __future__ import annotations

import pytest


@pytest.mark.asyncio
class TestAuth:
    async def test_register_success(self, client):
        res = await client.post("/auth/register", json={"email": "testuser@example.com", "password": "strongpassword"})
        # у тебя сейчас эндпоинт возвращает 200; оставим допуск на 201
        assert res.status_code in (200, 201), f"Unexpected status: {res.status_code}, response: {res.text}"
        data = res.json()
        assert "access_token" in data

    async def test_register_duplicate_email(self, client):
        payload = {"email": "dupe@example.com", "password": "password"}
        first = await client.post("/auth/register", json=payload)
        assert first.status_code in (200, 201)

        second = await client.post("/auth/register", json=payload)
        assert second.status_code == 400
        assert second.json()["detail"] == "Пользователь уже существует"

    async def test_login_success(self, client):
        email = "loginuser@example.com"
        password = "mypassword"
        await client.post("/auth/register", json={"email": email, "password": password})

        res = await client.post("/auth/login", json={"email": email, "password": password})
        assert res.status_code == 200, f"Unexpected status: {res.status_code}, response: {res.text}"
        data = res.json()
        assert "access_token" in data

    async def test_login_wrong_password(self, client):
        email = "wrongpass@example.com"
        correct = "correctpass"
        wrong = "wrongpass"
        await client.post("/auth/register", json={"email": email, "password": correct})

        res = await client.post("/auth/login", json={"email": email, "password": wrong})
        assert res.status_code == 401
        assert res.json()["detail"] == "Неверный email или пароль"

    async def test_login_unknown_user(self, client):
        res = await client.post("/auth/login", json={"email": "nonexistent@example.com", "password": "anypass"})
        assert res.status_code == 401
        assert res.json()["detail"] == "Неверный email или пароль"

@pytest.mark.asyncio
async def test_login_with_invalid_token(client):
    res = await client.get("/articles/", headers={"Authorization": "Bearer invalid"})
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_register_invalid_email(client):
    res = await client.post("/auth/register", json={"email": "bademail", "password": "123456"})
    assert res.status_code == 422
