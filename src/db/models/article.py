from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.db.base import Base


class Article(Base):
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    image_key = Column(String, nullable=True)  # Ключ объекта в S3
    category_id = Column(ForeignKey("category.id"), nullable=False)
    author_id = Column(ForeignKey("user.id"), nullable=False)
    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    category = relationship("Category", backref="articles")
    author = relationship("User", backref="articles")

    # Создаём GIN-индекс для полнотекстового поиска (в миграции)
    __table_args__ = (
        Index(
            "ix_article_fulltext",
            "title", "content",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops", "content": "gin_trgm_ops"}
        ),
    )
