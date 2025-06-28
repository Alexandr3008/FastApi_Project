from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.article import Article


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
async def test_update_article_forbidden(client_auth: AsyncClient, session: AsyncSession):
    """
    Проверяем, что нельзя обновить чужую статью.
    """
    # Добавляем статью с author_id=9999
    article = Article(title="Test", content="Test", category_id=1, author_id=9999)
    session.add(article)
    await session.commit()
    await session.refresh(article)

    response = await client_auth.put(
        f"/articles/{article.id}",
        files={"title": (None, "Updated")},
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}, {response.text}"
    assert "Not authorized" in response.text

@pytest.mark.asyncio
async def test_update_article_no_data(client_auth: AsyncClient):
    """
    Проверяем обновление несуществующей статьи или с пустыми данными.
    """
    response = await client_auth.put("/articles/99999")
    assert response.status_code in (404, 422), f"Unexpected: {response.status_code}, {response.text}"
