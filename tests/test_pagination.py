from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_pagination_and_search(client_auth):
    # Создаём категорию
    resp_cat = await client_auth.post("/categories/", json={"name": "BlogCat"})
    assert resp_cat.status_code == 201, f"Create category failed: {resp_cat.status_code}, {resp_cat.text}"
    cat_id = resp_cat.json()["id"]

    # Создаём 25 статей
    for i in range(25):
        res = await client_auth.post(
            "/articles/",
            files={
                "title": (None, f"Article {i}"),
                "content": (None, f"Content {i}"),
                "category_id": (None, str(cat_id))
            }
        )
        assert res.status_code == 201, f"Create article failed: {res.status_code}, {res.text}"

    # Проверяем пагинацию: page_number=2, page_size=10 → должны быть статьи 10..19
    response = await client_auth.get("/articles/?page_number=2&page_size=10")
    assert response.status_code == 200, f"Pagination failed: {response.status_code}, {response.text}"
    data = response.json()
    assert data["meta"]["total_items"] == 25
    assert data["meta"]["total_pages"] == 3
    assert data["meta"]["page_number"] == 2
    assert len(data["items"]) == 10

    # Проверяем поиск: «Article 1» должно вернуть хотя бы одну статью
    response2 = await client_auth.get("/articles/?search=Article 1")
    assert response2.status_code == 200, f"Search failed: {response2.status_code}, {response2.text}"
    data2 = response2.json()
    assert data2["meta"]["total_items"] >= 1

@pytest.mark.asyncio
async def test_invalid_page_size(client_auth: AsyncClient):
    res = await client_auth.get("/articles/?page_number=1&page_size=1000")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_search_not_found(client_auth: AsyncClient):
    res = await client_auth.get("/articles/?search=NoSuchArticle")
    assert res.status_code == 200
    data = res.json()
    assert data["meta"]["total_items"] == 0
    assert data["items"] == []
