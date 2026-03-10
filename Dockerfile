# ============================================================
# Stage 1: Build React SPA
# ============================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --prefer-offline 2>/dev/null || npm install

COPY frontend/ .
RUN npm run build

# ============================================================
# Stage 2: Django production image
# ============================================================
FROM python:3.12-slim AS production

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

# Copy React build output into Django's static directory
# Django's collectstatic will pick this up via STATICFILES_DIRS
RUN mkdir -p static/spa staticfiles media
COPY --from=frontend-builder /frontend/dist/ ./static/spa/

EXPOSE 8000

CMD ["sh", "-c", \
  "python manage.py migrate_schemas --shared && \
   python manage.py migrate_schemas && \
   python manage.py collectstatic --noinput && \
   daphne -b 0.0.0.0 -p ${PORT:-8000} erp_system.asgi:application"]

# ============================================================
# Stage 3: Development image (hot-reload, no build step)
# ============================================================
FROM production AS development

ENV DEBUG=True
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
