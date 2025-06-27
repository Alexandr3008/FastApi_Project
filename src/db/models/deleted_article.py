from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from src.db.base import Base


class DeletedArticle(Base):
    id = Column(Integer, primary_key=True, index=True)
    original_id = Column(Integer, nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category_id = Column(ForeignKey("category.id"), nullable=False)
    author_id = Column(ForeignKey("user.id"), nullable=False)
    image_key = Column(String, nullable=True)
    deleted_at = Column(DateTime(timezone=True), server_default=func.now())
