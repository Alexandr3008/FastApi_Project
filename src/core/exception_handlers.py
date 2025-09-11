from __future__ import annotations

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.logging_config import logger


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions.

    Args:
        request: Incoming request
        exc: HTTP exception
    """
    logger.warning(f"HTTPException: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": "http_exception",
            "status": exc.status_code
        },
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors.

    Args:
        request: Incoming request
        exc: Validation error
    """
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

async def integrity_error_handler(request: Request, exc: IntegrityError):
    """
    Handle database integrity errors.

    Args:
        request: Incoming request
        exc: Integrity error
    """
    logger.error(f"IntegrityError: {exc!s}")
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Database constraint error",
            "code": "integrity_error",
            "status": 400
        },
    )

async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle Starlette HTTP exceptions.

    Args:
        request: Incoming request
        exc: Starlette HTTP exception
    """
    logger.warning(f"Starlette HTTPException: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": "starlette_http_exception",
            "status": exc.status_code
        },
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Handle unhandled exceptions.

    Args:
        request: Incoming request
        exc: Unhandled exception
    """
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {exc!s}",
            "code": "unhandled_exception",
            "status": 500
        },
    )
