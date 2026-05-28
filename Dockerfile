FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY apps /app/apps
COPY scripts /app/scripts
COPY docs /app/docs
COPY .env.example /app/.env.example

RUN pip install --upgrade pip && pip install .

EXPOSE 8000

CMD ["python", "-m", "rag_project", "serve-api", "--host", "0.0.0.0", "--port", "8000"]
