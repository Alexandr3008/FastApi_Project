from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from src.api.auth.schemas import Token, UserCreate
from src.core.security import create_access_token
from src.core.tasks import send_registration_email
from src.db.models.user import User
from src.db.session import get_async_session
from src.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_async_session)):
    """
    Register a new user and send a welcome email.

    - **user_data**: User data (email, password)
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
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=60 * 60 * 24,
        samesite="lax",
        secure=True
    )
    return response


@router.post("/login", response_model=Token)
async def login(
        form_data: UserCreate,
        db: AsyncSession = Depends(get_async_session)
):
    """
    Аутентификация пользователя. Возвращает JWT токен.

    - **form_data**: email и пароль пользователя
    """
    user = await UserService.authenticate(db, form_data.email, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    access_token = create_access_token(str(user.id))

    response = JSONResponse(
        content={"access_token": access_token, "token_type": "bearer"}
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=60 * 60 * 24,
        samesite="lax",
        secure=True
    )
    return response
