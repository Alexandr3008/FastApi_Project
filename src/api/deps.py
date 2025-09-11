from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging_config import logger
from src.db.models.user import User
from src.db.session import get_async_session
from src.services.user_service import UserService


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """
    Достаём токен из request.state.token (middleware уже сохранило его).
    Проверяем токен, ищем пользователя и валидируем его статус.
    """
    token: str | None = getattr(request.state, "token", None)
    if not token:
        logger.warning("Authentication failed: No access token found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )

    try:
        user = await UserService.get_user_from_token(db, token)
    except Exception as e:
        logger.error(f"Authentication error while decoding token: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    if not user:
        logger.warning("Authentication failed: No user found for token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )

    if not user.is_active:
        logger.warning(f"Authentication failed: User {user.id} is inactive")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
        )

    logger.debug(f"User authenticated: id={user.id}, email={user.email}")
    return user
