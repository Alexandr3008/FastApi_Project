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

from alembic import command
from alembic.config import Config as AlembicConfig

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.security import create_access_token, hash_password
from src.db.base import Base
from src.db.models.user import User
from src.db.session import get_async_session
from src.main import app
from tests.test_config import test_settings

# ========== DB SETUP ==========

DATABASE_URL = test_settings.DB_URL
engine_test = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionTestLocal = async_sessionmaker(engine_test, expire_on_commit=False)



@pytest_asyncio.fixture(scope="function")
async def session():
    async with AsyncSessionTestLocal() as session:
        yield session


# ========== CLIENT FIXTURES ==========

@pytest_asyncio.fixture()
async def client(session: AsyncSession):
    """
    FastAPI test client with overridden DB session.
    """
    async def override_get_session():
        yield session

    app.dependency_overrides[get_async_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture()
async def client_auth(client, create_user):
    """
    Authenticated client with Bearer token from freshly created user.
    """
    user = await create_user("test@example.com", "string")
    token = create_access_token(str(user.id))
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


# ========== UTILITY FIXTURES ==========
@pytest_asyncio.fixture
async def test_user():
    async with engine_test.connect() as conn:
        await conn.execute(
            text("INSERT INTO users (email, hashed_password, is_active) VALUES (:email, :password, :is_active)"),
            {"email": "test@example.com", "password": "hashed_password", "is_active": True}
        )
        await conn.commit()
    yield
    async with engine_test.connect() as conn:
        await conn.execute(text("DELETE FROM users WHERE email = :email"), {"email": "test@example.com"})
        await conn.commit()


@pytest_asyncio.fixture
async def create_user(session: AsyncSession):
    async def _create_user(email: str, password: str):
        user = User(
            email=email,
            hashed_password=hash_password(password),
            is_active=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    return _create_user


@pytest_asyncio.fixture
async def get_token(create_user):
    async def _get_token(email: str = "test@example.com", password: str = "string"):
        user = await create_user(email, password)
        return create_access_token(str(user.id))
    return _get_token
