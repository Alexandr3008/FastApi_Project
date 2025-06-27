from __future__ import annotations

import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_article_success(client, get_token, session):
    token = await get_token("user1@example.com", "password123")
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post("/articles", json={"title": "Test"}, headers=headers)
    assert response.status_code == 200
    # create category
    res = await client.post("/categories/", json={"name": "Tech"}, headers=headers)
    assert res.status_code == 201
    category_id = res.json()["id"]

    # create article
    res = await client.post(
        "/articles/",
        headers=headers,
        files={
            "title": (None, "Test Article"),
            "content": (None, "Test content"),
            "category_id": (None, str(category_id)),
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Test Article"
    assert data["content"] == "Test content"
    assert data["category_id"] == category_id


@pytest.mark.asyncio
async def test_create_article_invalid_category(client, get_token):
    token = await get_token("user2@example.com", "pass")
    headers = {"Cookie": f"access_token=Bearer {token}"}

    res = await client.post(
        "/articles/",
        headers=headers,
        files={
            "title": (None, "Broken"),
            "content": (None, "Test"),
            "category_id": (None, "9999"),  # invalid
        },
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "Category not found"


@pytest.mark.asyncio
async def test_list_articles_unauthorized():
    from src.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        res = await client.get("/articles/")
        assert res.status_code == 401
