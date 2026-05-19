FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /venv \
    && /venv/bin/pip install --upgrade pip \
    && /venv/bin/pip install -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=mr_doctor.settings \
    PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && addgroup --system app \
    && adduser --system --ingroup app app \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv
COPY --chown=app:app . .

RUN mkdir -p /app/staticfiles /app/media \
    && chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/healthz/ || exit 1

CMD ["sh", "-c", "python manage.py collectstatic --noinput && gunicorn mr_doctor.wsgi:application --bind 0.0.0.0:${PORT} --workers ${GUNICORN_WORKERS:-3} --threads ${GUNICORN_THREADS:-2} --timeout ${GUNICORN_TIMEOUT:-60} --access-logfile - --error-logfile -"]
