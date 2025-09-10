from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = None

        # 1) Пробуем из cookie
        token_cookie = request.cookies.get("access_token")
        if token_cookie and token_cookie.startswith("Bearer "):
            token = token_cookie.removeprefix("Bearer ").strip()

        # 2) Если нет, пробуем из заголовка
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.removeprefix("Bearer ").strip()

        request.state.token = token
        return await call_next(request)
