from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_create_category_duplicate(client_auth):
    # Первая попытка
    res = await client_auth.post("/categories/", json={"name": "Health"})
    assert res.status_code == 201, f"Unexpected status: {res.status_code}, response: {res.text}"

    # Вторая с тем же именем
    res = await client_auth.post("/categories/", json={"name": "Health"})
    assert res.status_code == 400, f"Unexpected status: {res.status_code}, response: {res.text}"
    assert res.json()["detail"] == "Category with this name already exists"


@pytest.mark.asyncio
async def test_list_categories(client_auth):
    res = await client_auth.get("/categories/")
    assert res.status_code == 200, f"Unexpected status: {res.status_code}, response: {res.text}"
    data = res.json()
    assert isinstance(data, list), f"Expected list, got: {type(data)}"

@pytest.mark.asyncio
async def test_create_category_with_empty_name(client_auth):
    res = await client_auth.post("/categories/", json={"name": ""})
    assert res.status_code in (400, 422)
