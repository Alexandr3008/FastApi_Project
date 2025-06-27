from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging():
    # Создаём директорию для логов, если не существует
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Конфигурация логгера
    logger = logging.getLogger("blog_api")
    logger.setLevel(logging.INFO)  # Уровень логов (INFO, DEBUG, WARNING, ERROR, CRITICAL)

    # Формат логов
    log_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # Файловый обработчик (с ротацией по дням)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_dir / "blog_api.log",
        when="midnight",
        interval=1,
        backupCount=7  # Хранить логи за 7 дней
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    return logger


# Инициализация логгера
logger = setup_logging()
