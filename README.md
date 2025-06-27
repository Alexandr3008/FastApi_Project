Инициализация Poetry
Настройка pre-commit и ruff
Docker & Docker Compose
Выполнить миграции Alembic
alembic revision --autogenerate -m "initial tables"
Вставить в файл миграции в папке versions, в функцию upgrade следующее:
op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
Выполнить миграции Alembic
alembic upgrade head
Запуск тестов

python scripts/test_migrate.py
pytest -q
