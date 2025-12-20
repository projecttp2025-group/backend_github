FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root

COPY ./app /app

ENV PYTHONPATH=/ 

RUN mkdir -p /logs && chmod 0777 /logs

# install pg client to allow waiting for postgres in entrypoint
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# copy wait-for-db script
COPY wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

WORKDIR /


CMD ["sh", "-c", "/wait-for-db.sh && uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT:-8000}"]