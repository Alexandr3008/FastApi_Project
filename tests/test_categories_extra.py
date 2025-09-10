from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_category_empty_name(client_auth: AsyncClient):
    res = await client_auth.post("/categories/", json={"name": ""})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_category_long_name(client_auth: AsyncClient):
    long_name = "A" * 300
    res = await client_auth.post("/categories/", json={"name": long_name})
    assert res.status_code == 422
