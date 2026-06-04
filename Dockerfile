FROM python:3.11-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt

COPY . .

FROM base AS api
RUN pip install --no-cache-dir -r requirements/api.txt
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS worker
RUN pip install --no-cache-dir -r requirements/worker.txt
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, json; r = urllib.request.urlopen('http://localhost:8000/health'); assert r.status == 200"
CMD ["celery", "-A", "src.worker.celery_app", "worker", "--loglevel=info", "--concurrency=4", "-Q", "ingestion,classification,extraction,persistence,search,matching,default"]

FROM base AS dev
RUN pip install --no-cache-dir -r requirements/api.txt -r requirements/worker.txt
CMD ["python", "-c", "print('dev container ready')"]
