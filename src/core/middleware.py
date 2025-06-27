from __future__ import annotations

from fastapi import HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.core.security import decode_access_token
from src.db.models.user import User
from src.db.session import get_async_session


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.cookies.get("access_token")
        request.state.user = None
        if token:
            raw_token = token.removeprefix("Bearer ").strip()
            user_id = decode_access_token(raw_token)
            if user_id:
                async for db in get_async_session():
                    user = await db.get(User, int(user_id))
                    if user and user.is_active:
                        request.state.user = user
                        break
        return await call_next(request)
