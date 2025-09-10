from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_create_article_success(client_auth):
    # Сначала создаём категорию
    res = await client_auth.post("/categories/", json={"name": "Tech"})
    assert res.status_code == 201, f"Unexpected status: {res.status_code}, response: {res.text}"
    category_id = res.json()["id"]

    # Создаём статью
    res = await client_auth.post(
        "/articles/",
        files={
            "title": (None, "Test Article"),
            "content": (None, "Test content"),
            "category_id": (None, str(category_id)),
        },
    )
    assert res.status_code == 201, f"Unexpected status: {res.status_code}, response: {res.text}"
    data = res.json()
    assert data["title"] == "Test Article"
    assert data["content"] == "Test content"
    assert data["category_id"] == category_id


@pytest.mark.asyncio
async def test_create_article_invalid_category(client_auth):
    res = await client_auth.post(
        "/articles/",
        files={
            "title": (None, "Broken"),
            "content": (None, "Test"),
            "category_id": (None, "9999"),  # несуществующая категория
        },
    )
    assert res.status_code == 400, f"Unexpected status: {res.status_code}, response: {res.text}"
    assert res.json()["detail"] == "Category not found"


@pytest.mark.asyncio
async def test_list_articles_unauthorized(client):
    # важен завершающий слэш, иначе можно словить редирект
    res = await client.get("/articles/")
    assert res.status_code == 401, f"Unexpected status: {res.status_code}, response: {res.text}"

@pytest.mark.asyncio
async def test_create_article_without_title(client_auth):
    res = await client_auth.post("/articles/", files={"content": (None, "No title")})
    assert res.status_code == 422

@pytest.mark.asyncio
async def test_delete_article_twice(client_auth):
    # Создаём категорию
    cat = await client_auth.post("/categories/", json={"name": "News"})
    cat_id = cat.json()["id"]

    # Создаём статью
    article = await client_auth.post("/articles/", files={
        "title": (None, "To delete"),
        "content": (None, "bye"),
        "category_id": (None, str(cat_id)),
    })
    article_id = article.json()["id"]

    # Удаляем первый раз
    res1 = await client_auth.delete(f"/articles/{article_id}")
    assert res1.status_code == 204

    # Удаляем второй раз
    res2 = await client_auth.delete(f"/articles/{article_id}")
    assert res2.status_code in (404, 400)
