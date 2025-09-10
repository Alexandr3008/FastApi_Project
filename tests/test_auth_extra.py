from __future__ import annotations

import time

import pytest
from httpx import AsyncClient
from jose import jwt

from src.config import Settings

settings = Settings()


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    res = await client.post("/auth/register", json={"email": "not-an-email", "password": "password123"})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    res = await client.post("/auth/register", json={"email": "short@example.com", "password": "123"})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_access_protected_without_token(client: AsyncClient):
    res = await client.get("/articles/")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_access_with_expired_token(client: AsyncClient):
    # Создаем токен с маленьким сроком жизни
    payload = {"sub": "1", "exp": int(time.time()) - 10}
    expired_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    headers = {"Authorization": f"Bearer {expired_token}"}
    res = await client.get("/articles/", headers=headers)
    assert res.status_code == 401
