from __future__ import annotations

import json
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.core.logging_config import logger
from src.db.models.category import Category
from src.db.models.user import User
from src.db.session import get_async_session
from src.schemas.article import ArticleCreate, ArticleRead, ArticleUpdate
from src.schemas.pagination import Page
from src.services.article_service import ArticleService
from src.utils.s3 import delete_image, get_image_url, upload_image

router = APIRouter(
    prefix="/articles",
    tags=["articles"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/", response_model=ArticleRead, status_code=status.HTTP_201_CREATED)
async def create_article(
        data: ArticleCreate = Depends(ArticleCreate.as_form),
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user),
        image: Optional[UploadFile] = File(default=None),
):
    """
    Create a new article.

    - **data**: Article data (title, content, category_id)
    - **image**: Optional image file upload
    """
    try:
        result = await db.execute(select(Category).where(Category.id == data.category_id))
        category = result.scalar_one_or_none()
        if not category:
            logger.warning(f"Category not found: category_id={data.category_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")

        image_key = None
        if image and image.filename:
            try:
                logger.debug(f"Uploading image: filename={image.filename}")
                image_key = await upload_image(image, image.filename)
            except Exception as e:
                logger.error(f"Image upload failed: {e!s}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"Failed to upload image: {e!s}")

        try:
            logger.debug(f"Calling ArticleService.create_article with image_key={image_key}")
            article = await ArticleService.create_article(
                db, data.title, data.content, data.category_id, current_user.id, image_key
            )
            logger.info(f"Article created: id={article.id}")
        except ValueError as e:
            if image_key:
                logger.debug(f"Rolling back image upload: image_key={image_key}")
                await delete_image(image_key)
            logger.error(f"Article creation failed: {e!s}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            if image_key:
                logger.debug(f"Rolling back image upload: image_key={image_key}")
                await delete_image(image_key)
            logger.error(f"Unexpected error in article creation: {e!s}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Failed to create article: {e!s}")

        image_url = await get_image_url(image_key) if image_key else None
        logger.debug(f"Image URL generated: {image_url}")
        data = ArticleRead.model_validate(article).model_copy(update={"image_url": image_url})
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_article: {e!s}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/", response_model=Page[ArticleRead])
async def list_articles(
        search: Optional[str] = Query(None),
        category_id: Optional[int] = Query(None),
        page_number: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=50),
        db: AsyncSession = Depends(get_async_session),
):
    """
    List articles with optional search and category filter.

    - **search**: Optional search query for full-text search
    - **category_id**: Optional category filter
    - **page_number**: Page number (min 1)
    - **page_size**: Items per page (1 to 50)
    """
    logger.info(
        f"Listing articles: search={search}, category_id={category_id}, "
        f"page_number={page_number}, page_size={page_size}"
    )
    data = await ArticleService.list_articles(db, search, category_id, page_number, page_size)
    items = []
    for art in data["items"]:
        url = await get_image_url(art.image_key)
        art_read = ArticleRead.model_validate(art)
        items.append(art_read.model_copy(update={"image_url": url}))
    logger.debug(f"Retrieved {len(items)} articles")
    return Page[ArticleRead](items=items, meta=data["meta"])


@router.get("/{article_id}", response_model=ArticleRead)
async def get_article(
        article_id: int,
        db: AsyncSession = Depends(get_async_session)
):
    """
    Get a specific article by ID.

    - **article_id**: ID of the article
    """
    logger.info(f"Fetching article: article_id={article_id}")
    art = await ArticleService.get_article(db, article_id)
    if not art:
        logger.warning(f"Article not found: article_id={article_id}")
        raise HTTPException(status_code=404, detail="Статья не найдена")
    art_read = ArticleRead.model_validate(art)
    image_url = await get_image_url(art.image_key) if art.image_key else None
    return art_read.model_copy(update={"image_url": image_url})


@router.put("/{article_id}", response_model=ArticleRead)
async def update_article(
    article_id: int,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Update an article (multipart/form-data).
    You can update any field or upload a new image.
    """
    logger.info(f"Updating article: article_id={article_id}")

    art = await ArticleService.get_article(db, article_id)
    if not art:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    if art.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this article")

    update_data = {}
    if title is not None:
        update_data["title"] = title
    if content is not None:
        update_data["content"] = content
    if category_id is not None:
        update_data["category_id"] = category_id

    if not update_data and not image:
        raise HTTPException(
            status_code=422, detail="At least one field or image must be provided"
        )

    if image and image.filename:
        try:
            logger.debug(f"Uploading new image: {image.filename}")
            if art.image_key:
                await delete_image(art.image_key)
            new_image_key = await upload_image(image, image.filename)
            update_data["image_key"] = new_image_key
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image upload failed: {e!s}")

    try:
        updated_art = await ArticleService.update_article(db, article_id, **update_data)
        image_url = await get_image_url(updated_art.image_key) if updated_art.image_key else None
        return ArticleRead.model_validate(updated_art).model_copy(update={"image_url": image_url})
    except Exception as e:
        if "image_key" in update_data:
            await delete_image(update_data["image_key"])
        raise HTTPException(status_code=400, detail=f"Failed to update article: {e!s}")

@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
        article_id: int,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user),
):
    """
    Delete an article (soft delete).

    - **article_id**: ID of the article
    """
    try:
        logger.info(f"Deleting article: article_id={article_id}")
        article = await ArticleService.get_article(db, article_id)
        if not article:
            logger.warning(f"Article not found: article_id={article_id}")
            raise HTTPException(status_code=404, detail="Статья не найдена")
        if article.author_id != current_user.id:
            logger.warning(f"Unauthorized delete attempt: article_id={article_id}, user_id={current_user.id}")
            raise HTTPException(status_code=403, detail="Not authorized to delete this article")

        if article.image_key:
            try:
                logger.debug(f"Deleting image: image_key={article.image_key}")
                await delete_image(article.image_key)
            except Exception as e:
                logger.warning(f"Failed to delete image {article.image_key}: {e!s}")

        success = await ArticleService.delete_article(db, article_id)
        if not success:
            logger.warning(f"Article deletion failed: article_id={article_id}")
            raise HTTPException(status_code=400, detail="Failed to delete article")
        logger.info(f"Article deleted: id={article_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in delete_article: {e!s}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to delete article: {e!s}")
