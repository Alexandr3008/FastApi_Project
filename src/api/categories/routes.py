from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.models.category import Category
from src.db.session import get_async_session
from src.schemas.category import CategoryCreate, CategoryRead
from src.services.category_service import CategoryService

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
        data: CategoryCreate,
        db: AsyncSession = Depends(get_async_session)
):
    """
    Create a new category.

    - **data**: Category data (name)
    """
    existing = await db.execute(select(Category).filter(Category.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Category with this name already exists")

    category = await CategoryService.create_category(db, data.name)
    return category


@router.get("/", response_model=list[CategoryRead])
async def list_categories(db: AsyncSession = Depends(get_async_session)):
    """
    List all categories.
    """
    categories = await CategoryService.list_categories(db)
    return categories
