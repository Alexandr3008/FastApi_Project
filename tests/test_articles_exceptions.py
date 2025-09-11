from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.article import Article
from src.db.models.user import User


@pytest.mark.asyncio
async def test_create_article_invalid_category(client_auth: AsyncClient):
    """
    Проверяем ошибку при создании статьи с несуществующей категорией.
    """
    response = await client_auth.post(
        "/articles/",
        files={
            "title": (None, "Test"),
            "content": (None, "Invalid"),
            "category_id": (None, "999"),
        },
    )
    assert response.status_code == 400, f"Expected 400, got {response.status_code}, {response.text}"
    assert "Category not found" in response.text


@pytest.mark.asyncio
async def test_update_article_forbidden(client_auth: AsyncClient, session: AsyncSession, create_user):
    """
    Нельзя обновить чужую статью.
    """
    # 1) создаём категорию нормальным API-вызовом
    cat_resp = await client_auth.post("/categories/", json={"name": "TmpCat"})
    assert cat_resp.status_code == 201
    cat_id = cat_resp.json()["id"]

    # 2) создаём "другого" пользователя напрямую в БД
    other_user = await create_user("other@example.com", "otherpass123")

    # 3) создаём статью напрямую от этого "другого" пользователя
    article = Article(
        title="Test",
        content="Test",
        category_id=cat_id,
        author_id=other_user.id
    )
    session.add(article)
    await session.commit()
    await session.refresh(article)

    # 4) пытаемся обновить статью под client_auth (он НЕ владелец)
    response = await client_auth.put(
        f"/articles/{article.id}",
        files={"title": (None, "Updated")},
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}, {response.text}"
    assert "Not authorized" in response.text


@pytest.mark.asyncio
async def test_update_article_no_data(client_auth: AsyncClient):
    """
    Обновление несуществующей статьи или без данных.
    """
    response = await client_auth.put("/articles/99999")
    assert response.status_code in (404, 422), f"Unexpected: {response.status_code}, {response.text}"
