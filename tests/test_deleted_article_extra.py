from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_restore_article_not_found(client_auth: AsyncClient):
    res = await client_auth.post("/articles/99999/restore")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_double_delete_article(client_auth: AsyncClient):
    # Создаем категорию и статью
    res_cat = await client_auth.post("/categories/", json={"name": "DoubleDelete"})
    cat_id = res_cat.json()["id"]

    res_art = await client_auth.post(
        "/articles/",
        files={"title": (None, "DD"), "content": (None, "DDC"), "category_id": (None, str(cat_id))},
    )
    art_id = res_art.json()["id"]

    # Первый раз удаляем
    res1 = await client_auth.delete(f"/articles/{art_id}")
    assert res1.status_code == 204

    # Второй раз удаляем — должно быть 400 или 404
    res2 = await client_auth.delete(f"/articles/{art_id}")
    assert res2.status_code in (400, 404)
