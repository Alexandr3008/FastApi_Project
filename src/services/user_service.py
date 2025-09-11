from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth.schemas import UserCreate
from src.core.security import decode_access_token, hash_password, verify_password
from src.db.models.user import User


class UserService:
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Создание нового пользователя с хешированием пароля."""
        user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
        """Аутентификация пользователя по email и паролю."""
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()
        if user and verify_password(password, user.hashed_password):
            return user
        return None

    @staticmethod
    async def get_user_from_token(db: AsyncSession, token: str) -> User | None:
        """Получение пользователя по JWT токену."""
        user_id = decode_access_token(token)
        if not user_id:
            return None
        result = await db.execute(select(User).filter(User.id == int(user_id)))
        return result.scalar_one_or_none()
