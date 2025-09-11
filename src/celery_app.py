from __future__ import annotations

from celery import Celery

from src.config import Settings

settings = Settings()
celery_app = Celery(
    __name__,
    broker=settings.CELERY_BROKER_URL,
    backend=None
)

# Подключаем все таски
import src.core.tasks  # noqa
