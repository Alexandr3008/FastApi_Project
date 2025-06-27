from __future__ import annotations

from contextlib import asynccontextmanager

import aiobotocore
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.articles.routes import router as articles_router
from src.api.auth.routes import router as auth_router
from src.api.categories.routes import router as categories_router
from src.config import Settings
from src.core.exception_handlers import (
    http_exception_handler,
    integrity_error_handler,
    starlette_http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from src.core.logging_config import logger
from src.core.middleware import AuthMiddleware
from src.utils.s3 import ensure_bucket

settings = Settings()
app = FastAPI(title="Marketplace Blog API")
app.add_middleware(AuthMiddleware)


async def init_minio():
    logger.info("Initializing MinIO bucket")
    session = aiobotocore.session.get_session()
    async with session.create_client(
        "s3",
        endpoint_url=f"http{'s' if settings.MINIO_USE_SSL else ''}://{settings.MINIO_ENDPOINT}",
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name="us-east-1",
    ) as client:
        await ensure_bucket(client, settings.MINIO_BUCKET)
    logger.debug("MinIO bucket initialized")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting")
    await init_minio()
    yield
    logger.info("Application shutting down")


app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(articles_router)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
