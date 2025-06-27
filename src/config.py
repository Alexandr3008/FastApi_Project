from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    POSTGRES_USER: str = Field(...)
    POSTGRES_PASSWORD: str = Field(...)
    POSTGRES_DB: str = Field(...)
    DATABASE_URL: str = Field(...)

    # JWT
    JWT_SECRET_KEY: str = Field(...)
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)

    # Celery / RabbitMQ
    RABBITMQ_USER: str = Field(...)
    RABBITMQ_PASSWORD: str = Field(...)
    CELERY_BROKER_URL: str = Field(...)

    # MinIO (S3)
    MINIO_ENDPOINT: str = Field(...)
    MINIO_ACCESS_KEY: str = Field(...)
    MINIO_SECRET_KEY: str = Field(...)
    MINIO_ROOT_USER: str = Field(...)
    MINIO_ROOT_PASSWORD: str = Field(...)
    MINIO_USE_SSL: bool = Field(default=False)
    MINIO_BUCKET: str = Field(...)

    # SMTP
    SMTP_HOST: str = Field(...)
    SMTP_PORT: int = Field(...)
    SMTP_USER: str = Field(...)
    SMTP_PASSWORD: str = Field(...)
