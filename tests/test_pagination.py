from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_pagination_and_search(client):
    await client.post("/auth/register", json={"email": "p@e.com", "password": "pwd123"})
    # Создаём категорию
    resp_cat = await client.post("/categories", json={"name": "BlogCat"})
    cat_id = resp_cat.json()["id"]

    # Создаём 25 статей
    for i in range(25):
        await client.post(
            "/articles",
            data={
                "title": f"Article {i}",
                "content": f"Содержимое {i}",
                "category_id": str(cat_id)
            }
        )

    # Paginate: page_size=10, page_number=2 → статьи 10..19
    response = await client.get("/articles?page_number=2&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_items"] == 25
    assert data["meta"]["total_pages"] == 3
    assert data["meta"]["page_number"] == 2
    assert len(data["items"]) == 10

    # Поиск по «Article 1» вернёт хотя бы одну статью
    response2 = await client.get("/articles?search=Article 1")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["meta"]["total_items"] >= 1
