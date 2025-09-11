from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from src.core.logging_config import logger
from src.db.models.article import Article
from src.db.models.deleted_article import DeletedArticle
from src.db.models.user import User
from src.utils.pagination import paginate_query
from src.utils.search import apply_fulltext_search


class ArticleService:
    @staticmethod
    async def create_article(
            db: AsyncSession,
            title: str,
            content: str,
            category_id: int,
            author_id: int,
            image_key: str | None = None
    ):
        logger.info(f"Creating article in DB: title={title}, author_id={author_id}, category_id={category_id}")
        try:
            result = await db.execute(select(User).where(User.id == author_id))
            if not result.scalar_one_or_none():
                logger.error(f"Author not found: author_id={author_id}")
                raise ValueError("Author not found")

            article = Article(
                title=title,
                content=content,
                category_id=category_id,
                author_id=author_id,
                image_key=image_key,
                is_deleted=False
            )
            db.add(article)
            await db.commit()
            await db.refresh(article)
            logger.debug(f"Article saved: id={article.id}")
            return article
        except IntegrityError as e:
            logger.error(f"Database integrity error: {e!s}")
            await db.rollback()
            raise ValueError(f"Database error: {e!s}")
        except Exception as e:
            logger.error(f"Unexpected error in create_article: {e!s}")
            await db.rollback()
            raise

    @staticmethod
    async def get_article(db: AsyncSession, article_id: int):
        logger.info(f"Fetching article from DB: article_id={article_id}")
        result = await db.execute(
            select(Article).where(Article.id == article_id, Article.is_deleted == False)
        )
        article = result.scalar_one_or_none()
        if not article:
            logger.warning(f"Article not found in DB: article_id={article_id}")
        return article

    @staticmethod
    async def list_articles(
            db: AsyncSession,
            search: str | None,
            category_id: int | None,
            page_number: int,
            page_size: int
    ):
        logger.info(
            f"Listing articles in DB: search={search}, category_id={category_id}, "
            f"page_number={page_number}, page_size={page_size}"
        )
        query = select(Article).where(Article.is_deleted == False)
        if search:
            query = apply_fulltext_search(query, search)
        if category_id:
            query = query.where(Article.category_id == category_id)
        result = await paginate_query(db, query, page_number, page_size)
        logger.debug(f"Retrieved {len(result['items'])} articles from DB")
        return result

    @staticmethod
    async def update_article(db: AsyncSession, article_id: int, **kwargs):
        logger.info(f"Updating article in DB: article_id={article_id}, data={kwargs}")
        article = await ArticleService.get_article(db, article_id)
        if not article:
            logger.warning(f"Article not found for update: article_id={article_id}")
            return None
        try:
            for key, value in kwargs.items():
                setattr(article, key, value)
            article.updated_at = func.now()
            await db.commit()
            await db.refresh(article)
            logger.debug(f"Article updated: id={article.id}")
            return article
        except IntegrityError as e:
            logger.error(f"Database integrity error in update: {e!s}")
            await db.rollback()
            raise ValueError(f"Database error: {e!s}")
        except Exception as e:
            logger.error(f"Unexpected error in update_article: {e!s}")
            await db.rollback()
            raise

    @staticmethod
    async def delete_article(db: AsyncSession, article_id: int):
        logger.info(f"Deleting article in DB: article_id={article_id}")
        article = await ArticleService.get_article(db, article_id)
        if not article:
            logger.warning(f"Article not found for deletion: article_id={article_id}")
            return False
        try:
            deleted_article = DeletedArticle(
                original_id=article.id,
                title=article.title,
                content=article.content,
                category_id=article.category_id,
                author_id=article.author_id,
                image_key=article.image_key
            )
            db.add(deleted_article)
            article.is_deleted = True
            await db.commit()
            logger.debug(f"Article marked as deleted: id={article_id}")
            return True
        except IntegrityError as e:
            logger.error(f"Database integrity error in delete_article: {e!s}")
            await db.rollback()
            raise ValueError(f"Database error: {e!s}")
        except Exception as e:
            logger.error(f"Unexpected error in delete_article: {e!s}")
            await db.rollback()
            raise

    @staticmethod
    async def list_deleted_articles(db: AsyncSession, user_id: int):
        result = await db.execute(
            select(Article).where(Article.author_id == user_id, Article.is_deleted == True)
        )
        return result.scalars().all()

    @staticmethod
    async def restore_article(db: AsyncSession, article_id: int, user_id: int):
        result = await db.execute(
            select(Article).where(Article.id == article_id, Article.author_id == user_id, Article.is_deleted == True)
        )
        article = result.scalar_one_or_none()
        if not article:
            return None
        article.is_deleted = False
        await db.commit()
        await db.refresh(article)
        return article
