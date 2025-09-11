

docker-compose up -d --build
Инициализация Poetry
poetry install --with dev
Настройка pre-commit и ruff
Docker & Docker Compose
Выполнить миграции Alembic
alembic -c alembic.ini revision --autogenerate -m "initial tables"
Вставить в файл миграции в папке alembic/versions, в функцию upgrade следующее:
op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
Выполнить миграции Alembic
alembic -c alembic.ini upgrade head

Запуск тестов
В файле alembic.ini изменить sqlalchemy.url на тестовый
Выполнить миграции Alembic
alembic -c tests/alembic.ini revision --autogenerate -m "initial tables"
Вставить в файл миграции в папке tests/alembic/versions, в функцию upgrade следующее:
op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
Выполнить миграции Alembic
alembic -c tests/alembic.ini upgrade head

Установить библиотеки для тестирования
poetry install --with dev
Запустить тесты
pytest -q
