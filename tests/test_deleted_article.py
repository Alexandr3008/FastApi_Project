from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.article import Article


@pytest.mark.asyncio
async def test_soft_delete_article(client_auth: AsyncClient, session: AsyncSession):
    """
    Проверяем, что статья при удалении не исчезает насовсем,
    а в БД у неё проставляется is_deleted=True.
    """
    # Создаем категорию
    res_cat = await client_auth.post("/categories/", json={"name": "SoftDelete"})
    assert res_cat.status_code == 201
    category_id = res_cat.json()["id"]

    # Создаем статью
    res_art = await client_auth.post(
        "/articles/",
        files={
            "title": (None, "SoftDelete Article"),
            "content": (None, "Content"),
            "category_id": (None, str(category_id)),
        },
    )
    assert res_art.status_code == 201
    article_id = res_art.json()["id"]

    # Удаляем статью
    res_del = await client_auth.delete(f"/articles/{article_id}")
    assert res_del.status_code == 204

    # Проверяем, что в списке активных её нет
    res_list = await client_auth.get("/articles/")
    assert all(a["id"] != article_id for a in res_list.json()["items"])

    # Проверяем напрямую в БД
    article = await session.get(Article, article_id)
    assert article is not None
    assert article.is_deleted is True

@pytest.mark.asyncio
async def test_restore_deleted_article(client_auth: AsyncClient, session: AsyncSession):
    """
    Проверяем восстановление статьи из deleted_article.
    """
    # Создаём категорию
    res_cat = await client_auth.post("/categories/", json={"name": "To Restore"})
    assert res_cat.status_code == 201
    category_id = res_cat.json()["id"]

    # Создаём статью
    res_art = await client_auth.post(
        "/articles/",
        files={
            "title": (None, "To Restore"),
            "content": (None, "Content"),
            "category_id": (None, str(category_id)),
        },
    )
    assert res_art.status_code == 201
    article_id = res_art.json()["id"]

    # Удаляем статью
    res_del = await client_auth.delete(f"/articles/{article_id}")
    assert res_del.status_code == 204

    # Восстанавливаем статью
    res_restore = await client_auth.post(f"/articles/{article_id}/restore")
    assert res_restore.status_code == 200
    restored = res_restore.json()
    assert restored["id"] == article_id
    assert restored["title"] == "To Restore"

    # 🔹 Проверяем в БД через session
    article = await session.get(Article, article_id)
    assert article is not None
    assert article.is_deleted is False
