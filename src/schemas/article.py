from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import Form
from pydantic import BaseModel, ValidationError, model_validator


class ArticleBase(BaseModel):
    title: str
    content: str
    category_id: int

class ArticleCreate(ArticleBase):
    @classmethod
    def as_form(
            cls,
            title: str = Form(...),
            content: str = Form(...),
            category_id: int = Form(...),
    ) -> "ArticleCreate":
        return cls(title=title, content=content, category_id=category_id)

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def check_at_least_one_field(cls, values):
        """
        Ensure at least one field is provided.
        """
        if isinstance(values, dict) and not any(v is not None for v in values.values()):
            raise ValueError("At least one field must be provided")
        return values

class ArticleRead(ArticleBase):
    id: int
    image_key: Optional[str] = None
    image_url: Optional[str] = None
    author_id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
