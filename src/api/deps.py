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
    Получение текущего пользователя из токена, хранящегося в cookies.
    """
    try:
        token = request.cookies.get("access_token")
        if not token:
            logger.warning("Authentication failed: No access token in cookies")
            raise HTTPException(status_code=401, detail="Invalid or missing token")
        raw_token = token.removeprefix("Bearer ").strip()
        user = await UserService.get_user_from_token(db, raw_token)
        if not user:
            logger.warning("Authentication failed: No user found for token")
            raise HTTPException(status_code=401, detail="Invalid or missing token")

        if not user.is_active:
            logger.warning(f"Authentication failed: User {user.id} is inactive")
            raise HTTPException(status_code=401, detail="Inactive user")

        logger.debug(f"User authenticated: id={user.id}, email={user.email}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e!s}")
        raise HTTPException(status_code=401, detail="Authentication failed")
