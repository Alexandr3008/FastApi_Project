from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class PageMeta(BaseModel):
    page_number: int
    page_size: int
    total_items: int
    total_pages: int

class Page(BaseModel, Generic[T]):
    items: List[T]
    meta: PageMeta
