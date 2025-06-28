from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings_Test(BaseSettings):
    # FastAPI
    BASE_URL: str = "http://test"

    # Тестовая база данных (PostgreSQL)
    DB_URL: str = "postgresql+asyncpg://test_user:test_pass@db_test:5432/test_db"

    # MinIO
    MINIO_ENDPOINT: str = "minio_test:9001"
    MINIO_ACCESS_KEY: str = "testminio"
    MINIO_SECRET_KEY: str = "testminio123"
    MINIO_BUCKET: str = "test-bucket"
    MINIO_USE_SSL: bool = False



test_settings = Settings_Test()
