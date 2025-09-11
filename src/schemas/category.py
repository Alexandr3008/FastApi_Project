from __future__ import annotations

from pydantic import BaseModel, StringConstraints
from typing_extensions import Annotated


class CategoryCreate(BaseModel):
    name: Annotated[str, StringConstraints(min_length=1, max_length=100, strip_whitespace=True)]

class CategoryRead(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
