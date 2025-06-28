from __future__ import annotations

import asyncio
import os
import sys

import pytest
import pytest_asyncio
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.security import hash_password
from src.db.models.user import User
from src.db.session import get_async_session
from src.main import app
from tests.test_config import test_settings

DATABASE_URL = test_settings.DB_URL
engine_test = create_async_engine(DATABASE_URL, echo=False, future=True)
TestSessionLocal = async_sessionmaker(bind=engine_test, expire_on_commit=False)

CLEAN_TABLES = ["article", "user", "category"]

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def async_session_test():
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield async_session

@pytest.fixture(scope="function", autouse=True)
async def clean_tables(async_session_test):
    """Clean data in all tables before running test function"""
    async with async_session_test() as session:
        async with session.begin():
            for table_for_cleaning in CLEAN_TABLES:
                await session.execute(text(f"""TRUNCATE TABLE {table_for_cleaning} RESTART IDENTITY CASCADE;"""))

@pytest_asyncio.fixture
async def session() -> AsyncSession:
    async with TestSessionLocal() as test_session:
        yield test_session

@pytest_asyncio.fixture
async def client():
    """
    Каждый запрос в тестах будет использовать новую сессию.
    """
    async def override_get_session():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.pop(get_async_session, None)

@pytest_asyncio.fixture
async def create_user(session: AsyncSession):
    async def _create_user(email: str, password: str):
        user = User(email=email, hashed_password=hash_password(password), is_active=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    return _create_user

@pytest_asyncio.fixture
async def get_token(client):
    """
    Регистрирует и логинит, возвращает токен (из body, не куки).
    """
    async def _get_token(email="default@example.com", password="password123"):
        await client.post("/auth/register", json={"email": email, "password": password})
        response = await client.post("/auth/login", json={"email": email, "password": password})
        data = response.json()
        return data["access_token"]
    return _get_token

@pytest_asyncio.fixture
async def client_auth(client, get_token):
    token = await get_token()
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
