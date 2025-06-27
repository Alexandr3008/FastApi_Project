from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

T = TypeVar("T")

class PageMeta(BaseModel):
    page_number: int
    page_size: int
    total_items: int
    total_pages: int

class Page(BaseModel, Generic[T]):
    items: List[T]
    meta: PageMeta

async def paginate_query(
    db: AsyncSession,
    query: Select,
    page_number: int,
    page_size: int
) -> dict:
    """
    Paginate a SQLAlchemy query.

    Args:
        db: Database session
        query: SQLAlchemy query
        page_number: Page number (must be positive)
        page_size: Items per page (must be positive)

    Returns:
        dict: Paginated results with items and metadata

    Raises:
        ValueError: If page_number or page_size is not positive
    """
    if page_number < 1:
        raise ValueError("Page number must be positive")
    if page_size < 1:
        raise ValueError("Page size must be positive")

    total_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(total_query)
    total_items = total_res.scalar_one()
    total_pages = (total_items + page_size - 1) // page_size

    offset = (page_number - 1) * page_size
    paginated = query.offset(offset).limit(page_size)
    result = await db.execute(paginated)
    items = result.scalars().all()

    return {
        "items": items,
        "meta": {
            "page_number": page_number,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
        },
    }
