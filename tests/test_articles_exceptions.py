from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.article import Article


@pytest.mark.asyncio
async def test_create_article_invalid_category(client_auth: AsyncClient):
    response = await client_auth.post(
        "/articles/",
        data={"title": "Test", "content": "Invalid", "category_id": 999},
    )
    assert response.status_code == 400
    assert "Category not found" in response.text


@pytest.mark.asyncio
async def test_update_article_forbidden(client_auth: AsyncClient, session: AsyncSession):
    # создаём статью от имени другого пользователя
    article = Article(
        title="Test", content="Test", category_id=1, author_id=9999
    )
    session.add(article)
    await session.commit()
    await session.refresh(article)

    response = await client_auth.put(f"/articles/{article.id}", data={"title": "Updated"})
    assert response.status_code == 403
    assert "Not authorized" in response.text


@pytest.mark.asyncio
async def test_update_article_no_data(client_auth: AsyncClient, session: AsyncSession):
    response = await client_auth.put("/articles/99999")
    assert response.status_code in (404, 422)
