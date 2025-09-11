from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_article_with_image(client_auth: AsyncClient, tmp_path):
    # Создаем категорию
    res_cat = await client_auth.post("/categories/", json={"name": "WithImage"})
    assert res_cat.status_code == 201
    category_id = res_cat.json()["id"]

    # Фейковое изображение
    file_path = tmp_path / "test.png"
    file_path.write_bytes(b"fake image content")

    with file_path.open("rb") as f:
        res = await client_auth.post(
            "/articles/",
            data={"title": "Article with Image", "content": "Content", "category_id": str(category_id)},
            files={"image": ("test.png", f, "image/png")},
        )

    assert res.status_code == 201, res.text
    data = res.json()
    assert data["title"] == "Article with Image"
    assert data["image_url"] is not None


@pytest.mark.asyncio
async def test_update_article_only_image(client_auth: AsyncClient, tmp_path):
    # Создаем категорию
    res_cat = await client_auth.post("/categories/", json={"name": "UpdateImage"})
    category_id = res_cat.json()["id"]

    # Создаем статью
    res_art = await client_auth.post(
        "/articles/",
        files={"title": (None, "Article"), "content": (None, "Old content"), "category_id": (None, str(category_id))},
    )
    article_id = res_art.json()["id"]

    # Загружаем новое изображение
    new_file = tmp_path / "new.png"
    new_file.write_bytes(b"new fake image")

    with new_file.open("rb") as f:
        res = await client_auth.put(
            f"/articles/{article_id}",
            files={"image": ("new.png", f, "image/png")},
        )

    assert res.status_code == 200, res.text
    data = res.json()
    assert data["image_url"] is not None


@pytest.mark.asyncio
async def test_update_article_invalid_category(client_auth: AsyncClient):
    # Создаем категорию и статью
    res_cat = await client_auth.post("/categories/", json={"name": "InvalidCat"})
    category_id = res_cat.json()["id"]
    res_art = await client_auth.post(
        "/articles/",
        files={"title": (None, "Art"), "content": (None, "Cont"), "category_id": (None, str(category_id))},
    )
    article_id = res_art.json()["id"]

    # Пытаемся обновить с несуществующей категорией
    res = await client_auth.put(f"/articles/{article_id}", files={"category_id": (None, "99999")})
    assert res.status_code == 400 or res.status_code == 422
