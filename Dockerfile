# Multi-stage build: one image for CI (lint + tests), one slim image for runtime.

# ---------- base: Python + production dependencies ----------
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---------- test: adds dev tools; used by Jenkins to run flake8 + pytest ----------
FROM base AS test
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
COPY . .
CMD ["sh", "-c", "flake8 . && pytest"]

# ---------- runtime: only what is needed to serve the app ----------
FROM base AS runtime
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION} \
    DATABASE_PATH=/data/aceest.db \
    PORT=8000
# Non-root user; /data is the persistent SQLite location (mount a volume here).
RUN useradd --system --uid 10001 --no-create-home aceest \
    && mkdir /data && chown aceest /data
COPY app ./app
COPY wsgi.py .
USER 10001
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
# One worker + threads: SQLite allows a single writer, so extra processes add nothing.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --access-logfile - wsgi:app"]
