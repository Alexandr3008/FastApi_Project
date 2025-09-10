from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth.schemas import Token, UserCreate
from src.core.security import create_access_token
from src.core.tasks import send_registration_email
from src.db.models.user import User
from src.db.session import get_async_session
from src.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


def set_token_cookie(response: JSONResponse, access_token: str) -> None:
    """Устанавливает JWT в cookie (HttpOnly)."""
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=60 * 60 * 24,  # 1 день
        samesite="lax",
        secure=False,  # ⚠️ Для локальной разработки ставим False, в проде лучше True
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_async_session)):
    """
    Регистрация нового пользователя и отправка приветственного письма.
    """
    existing = await db.execute(select(User).filter(User.email == user_data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")

    user = await UserService.create_user(db, user_data)
    send_registration_email.delay(user.email)

    access_token = create_access_token(str(user.id))
    response = JSONResponse(
        content={"access_token": access_token, "token_type": "bearer"}
    )
    set_token_cookie(response, access_token)
    return response


@router.post("/login", response_model=Token)
async def login(form_data: UserCreate, db: AsyncSession = Depends(get_async_session)):
    """
    Логин пользователя, выдаёт JWT токен в cookie + JSON.
    """
    user = await UserService.authenticate(db, form_data.email, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    access_token = create_access_token(str(user.id))
    response = JSONResponse(
        content={"access_token": access_token, "token_type": "bearer"}
    )
    set_token_cookie(response, access_token)
    return response

@router.post("/logout")
async def logout(response: JSONResponse):
    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie("access_token")
    return response
