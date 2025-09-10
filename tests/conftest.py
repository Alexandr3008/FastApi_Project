from __future__ import annotations

import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.security import hash_password
from src.db.models.user import User
from src.db.session import get_async_session
from src.main import app
from tests.test_config import test_settings

DATABASE_URL = test_settings.DB_URL
engine_test = create_async_engine(DATABASE_URL, future=True, echo=False)


# ============================================================
# Event loop общий для тестов
# ============================================================
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================
# Engine + session (function scope!)
# ============================================================
@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(test_settings.DB_URL, future=True, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session


# ============================================================
# Очистка таблиц перед каждым тестом
# ============================================================
@pytest_asyncio.fixture(autouse=True)
async def clean_tables(engine):
    async with engine.begin() as conn:
        await conn.execute(
            text('TRUNCATE TABLE "deletedarticle", "article", "category", "user" RESTART IDENTITY CASCADE;')
        )

# ============================================================
# Очистка таблиц после всех тестов
# ============================================================

@pytest.fixture(scope="session", autouse=True)
async def cleanup_after_tests():
    """
    После выполнения всех тестов очищает все таблицы в тестовой БД.
    """
    yield  # ждём пока пройдут все тесты

    async with engine_test.begin() as conn:
        await conn.execute(text('TRUNCATE TABLE deletedarticle, article, category, "user" RESTART IDENTITY CASCADE;'))

# ============================================================
# HTTP client с заменой зависимостей
# ============================================================
@pytest_asyncio.fixture
async def client(engine):
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_session() -> AsyncSession:
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.pop(get_async_session, None)


# ============================================================
# Утилиты для тестов
# ============================================================
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
async def get_token(client: AsyncClient):
    async def _get_token(email="default@example.com", password="password123"):
        await client.post("/auth/register", json={"email": email, "password": password})
        res = await client.post("/auth/login", json={"email": email, "password": password})
        return res.json()["access_token"]

    return _get_token


@pytest_asyncio.fixture
async def client_auth(client: AsyncClient):
    """
    Клиент с авторизацией через cookie.
    """
    email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    password = "password123"

    # Регистрируем пользователя
    res = await client.post("/auth/register", json={"email": email, "password": password})
    assert res.status_code in (200, 201), res.text

    # Логинимся → сервер вернёт JWT в cookie
    res_login = await client.post("/auth/login", json={"email": email, "password": password})
    assert res_login.status_code == 200, res_login.text

    # Переносим куки из ответа в клиент
    client.cookies.update(res_login.cookies)

    return client
