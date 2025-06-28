Инициализация Poetry
poetry install --with dev
Настройка pre-commit и ruff
Docker & Docker Compose
Выполнить миграции Alembic
alembic revision --autogenerate -m "initial tables"
Вставить в файл миграции в папке versions, в функцию upgrade следующее:
op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
Выполнить миграции Alembic
alembic upgrade head

Запуск тестов
В файле alembic.ini изменить sqlalchemy.url на тестовый
Выполнить миграции Alembic
alembic revision --autogenerate -m "initial tables"
alembic upgrade head
В файле alembic.ini изменить sqlalchemy.url на основной
Установить библиотеки для тестирования
poetry install --with dev
Запустить тесты
pytest -q
