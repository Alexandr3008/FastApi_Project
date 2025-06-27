from __future__ import annotations

import asyncio
import os

from alembic import command
from alembic.config import Config

if __name__ == "__main__":
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://test_user:test_pass@db_test:5432/test_db"

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
    command.upgrade(alembic_cfg, "head")
