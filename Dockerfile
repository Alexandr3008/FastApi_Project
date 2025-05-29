FROM python:3.12-slim

# Устанавливаем зависимости ОС (для psycopg2, aiobotocore и т.д.)
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock /app/
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

COPY src/ /app/src/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/

ENV PYTHONPATH=/app/src
ENV APP_MODULE=src.main:app

# Открываем порт
EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
