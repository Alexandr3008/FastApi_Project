from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ArticleBase(BaseModel):
    title: str
    content: str
    category_id: int

class ArticleCreate(ArticleBase):
    pass  # все поля берутся из базового

class ArticleUpdate(BaseModel):
    title: Optional[str]
    content: Optional[str]
    category_id: Optional[int]
    # Изображение будем передавать через form-data отдельно

class ArticleRead(BaseModel):
    id: int
    title: str
    content: str
    category_id: int
    author_id: int
    image_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
