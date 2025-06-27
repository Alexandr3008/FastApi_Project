from __future__ import annotations

from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    # FastAPI
    BASE_URL: str = "http://test"

    # Тестовая база данных (PostgreSQL)
    DB_HOST: str = "db_test"
    DB_PORT: int = 5432
    DB_NAME: str = "test_db"
    DB_USER: str = "test_user"
    DB_PASS: str = "test_pass"
    DB_URL: str = "postgresql+asyncpg://test_user:test_pass@db_test:5432/test_db"

    # JWT
    JWT_SECRET_KEY: str = "test_secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # MinIO
    MINIO_ENDPOINT: str = "minio_test:9001"
    MINIO_ACCESS_KEY: str = "testminio"
    MINIO_SECRET_KEY: str = "testminio123"
    MINIO_BUCKET: str = "test-bucket"
    MINIO_USE_SSL: bool = False


    class Config:
        env_file = ".env.test"
        env_file_encoding = "utf-8"


test_settings = TestSettings()
