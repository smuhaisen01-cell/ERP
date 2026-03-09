FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libxml2-dev libxslt1-dev \
    libssl-dev libffi-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY manage.py .
COPY erp_system/ ./erp_system/
COPY apps/ ./apps/
COPY scripts/ ./scripts/

RUN mkdir -p staticfiles media

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate_schemas --shared && python manage.py migrate_schemas && python manage.py collectstatic --noinput && daphne -b 0.0.0.0 -p ${PORT:-8000} erp_system.asgi:application"]
