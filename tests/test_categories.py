from __future__ import annotations

import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_category_duplicate(client, get_token):
    token = await get_token("user3@example.com", "123456")
    headers = {"Cookie": f"access_token=Bearer {token}"}

    res = await client.post("/categories/", json={"name": "Health"}, headers=headers)
    assert res.status_code == 201

    # Try duplicate
    res = await client.post("/categories/", json={"name": "Health"}, headers=headers)
    assert res.status_code == 400
    assert res.json()["detail"] == "Category with this name already exists"


@pytest.mark.asyncio
async def test_list_categories(client, get_token):
    token = await get_token("user4@example.com", "123"),
    headers = {"Cookie": f"access_token=Bearer {token[0]}"}
    res = await client.get("/categories/", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
