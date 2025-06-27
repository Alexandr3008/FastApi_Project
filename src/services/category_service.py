from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.category import Category


class CategoryService:
    @staticmethod
    async def create_category(db: AsyncSession, name: str) -> Category:
        """
        Create a new category.

        Args:
            db: Database session
            name: Category name

        Returns:
            Category: Created category

        Raises:
            HTTPException: If category with this name already exists
        """
        existing = await db.execute(select(Category).filter(Category.name == name))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Category with this name already exists")

        category = Category(name=name)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def list_categories(db: AsyncSession) -> list[Category]:
        """
        List all categories.

        Args:
            db: Database session

        Returns:
            list[Category]: List of categories
        """
        result = await db.execute(select(Category))
        return result.scalars().all()
