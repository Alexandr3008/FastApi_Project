FROM python:3.12-slim
RUN pip install --upgrade pip
WORKDIR /app
RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock* README.md* /app/
RUN poetry config virtualenvs.create false && poetry install --only main --no-root --no-interaction --no-ansi
COPY . /app
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
