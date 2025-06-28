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
    Получение текущего пользователя из токена в заголовке Authorization или в cookies.
    """
    try:
        token = None

        # Сначала пробуем из заголовка
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
        else:
            # Потом из cookies
            cookie_token = request.cookies.get("access_token")
            if cookie_token and cookie_token.startswith("Bearer "):
                token = cookie_token.removeprefix("Bearer ").strip()

        if not token:
            logger.warning("Authentication failed: No access token found")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")

        user = await UserService.get_user_from_token(db, token)
        if not user:
            logger.warning("Authentication failed: No user found for token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")

        if not user.is_active:
            logger.warning(f"Authentication failed: User {user.id} is inactive")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

        logger.debug(f"User authenticated: id={user.id}, email={user.email}")
        return user

    except HTTPException:
        raise
    except Exception:
        logger.exception("Authentication unexpected error")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")
