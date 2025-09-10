from __future__ import annotations

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
from src.schemas.article import ArticleCreate, ArticleRead
from src.schemas.pagination import Page
from src.services.article_service import ArticleService
from src.utils.s3 import delete_image, get_image_url, upload_image

router = APIRouter(
    prefix="/articles",
    tags=["articles"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/", response_model=Page[ArticleRead])
async def list_articles(
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Список статей (только для авторизованных).
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
    db: AsyncSession = Depends(get_async_session),
):
    """
    Получить статью по ID (только для авторизованных).
    """
    logger.info(f"Fetching article: article_id={article_id}")
    art = await ArticleService.get_article(db, article_id)
    if not art:
        logger.warning(f"Article not found: article_id={article_id}")
        raise HTTPException(status_code=404, detail="Статья не найдена")
    art_read = ArticleRead.model_validate(art)
    image_url = await get_image_url(art.image_key) if art.image_key else None
    return art_read.model_copy(update={"image_url": image_url})


@router.post("/", response_model=ArticleRead, status_code=status.HTTP_201_CREATED)
async def create_article(
    data: ArticleCreate = Depends(ArticleCreate.as_form),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    image: Optional[UploadFile] = File(default=None),
):
    """
    Создать новую статью (только авторизованный пользователь).
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

        article = await ArticleService.create_article(
            db, data.title, data.content, data.category_id, current_user.id, image_key
        )
        logger.info(f"Article created: id={article.id}")

        image_url = await get_image_url(image_key) if image_key else None
        return ArticleRead.model_validate(article).model_copy(update={"image_url": image_url})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_article: {e!s}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


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
    Обновить статью (только автор).
    """
    logger.info(f"Updating article: article_id={article_id}")
    art = await ArticleService.get_article(db, article_id)
    if not art:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    if art.author_id != current_user.id:
        logger.warning(f"Unauthorized update attempt: article_id={article_id}, user_id={current_user.id}")
        raise HTTPException(status_code=403, detail="Not authorized to modify this article")

    update_data = {}

    if title is not None:
        update_data["title"] = title
    if content is not None:
        update_data["content"] = content
    if category_id is not None:
        result = await db.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if not category:
            logger.warning(f"Category not found: category_id={category_id}")
            raise HTTPException(status_code=400, detail="Category not found")
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

    updated_art = await ArticleService.update_article(db, article_id, **update_data)
    image_url = await get_image_url(updated_art.image_key) if updated_art.image_key else None
    return ArticleRead.model_validate(updated_art).model_copy(update={"image_url": image_url})


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Удалить статью (soft delete, только автор).
    """
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
        raise HTTPException(status_code=400, detail="Failed to delete article")

    logger.info(f"Article deleted: id={article_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/deleted", response_model=list[ArticleRead])
async def list_deleted_articles(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Получить список удалённых статей (только свои).
    """
    logger.info(f"Listing deleted articles for user_id={current_user.id}")
    articles = await ArticleService.list_deleted_articles(db, current_user.id)
    result = []
    for art in articles:
        url = await get_image_url(art.image_key)
        result.append(ArticleRead.model_validate(art).model_copy(update={"image_url": url}))
    return result


@router.post("/{article_id}/restore", response_model=ArticleRead)
async def restore_article(
    article_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Восстановить удалённую статью (только автор).
    """
    logger.info(f"Restoring article: article_id={article_id}, user_id={current_user.id}")
    article = await ArticleService.restore_article(db, article_id, current_user.id)
    if not article:
        raise HTTPException(status_code=404, detail="Статья не найдена или недоступна")
    url = await get_image_url(article.image_key)
    return ArticleRead.model_validate(article).model_copy(update={"image_url": url})
