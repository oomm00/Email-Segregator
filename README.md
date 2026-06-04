# Shipping Email Segregation & Data Extraction System

Event-driven platform for ingesting, classifying, and extracting structured shipping data from maritime emails.

## Architecture

```
Email Source → API → RabbitMQ → Worker → PostgreSQL / Elasticsearch / MinIO
```

| Service | Responsibility |
|---------|---------------|
| **api** | FastAPI REST gateway — receives emails, serves health/metrics |
| **worker** | Celery worker — processes events from RabbitMQ queues |
| **ingestion** | Deduplicates, stores raw emails, parses content (Phase 1) |
| **extraction** | Extracts structured records from classified emails (Phase 3) |
| **matching** | Matches records against known accounts/ports (Phase 4) |
| **postgres** | Primary operational data store |
| **redis** | Celery result backend + caching |
| **rabbitmq** | Event broker (topic exchange `shipping.email`) |
| **elasticsearch** | Full-text search over emails and records |
| **minio** | S3-compatible attachment storage |

## Event Flow

```
raw.email.received → email.parsed → email.classified → record.extracted → record.persisted → match.found
```

## Quick Start

```bash
# Clone and enter the project
cd shipping-email-system

# Copy environment config
cp .env.example .env

# Start all services
docker compose up --build

# Run database migrations
docker compose exec api alembic upgrade head

# Check health
curl http://localhost:8000/health
curl http://localhost:8000/ready

# Send a test email
curl -X POST http://localhost:8000/api/v1/inbound/email \
  -H "Content-Type: application/json" \
  -d '{"message_id":"<test@test.com>","sender":"a@b.com","recipients":["c@d.com"],"subject":"Test","body_text":"Hello"}'
```

## Local Development (without Docker)

```bash
python3.11 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements/base.txt -r requirements/api.txt -r requirements/worker.txt
pip install -e ".[dev]"
cp .env.example .env
# edit .env for local postgres/redis/rabbitmq
uvicorn src.api.main:app --reload
celery -A src.worker.celery_app worker --loglevel=info
```

## Project Structure

```
src/
├── common/          # Shared: config, DB, messaging, observability, storage
│   ├── config.py        # Pydantic-settings
│   ├── exceptions.py    # Base exceptions
│   ├── models/          # Domain models + event contracts (Pydantic)
│   ├── db/              # SQLAlchemy async engine, models, session
│   ├── messaging/       # Celery app + Kombu publishers
│   ├── observability/   # Logging (structlog), metrics, tracing
│   └── storage/         # MinIO client
├── api/             # FastAPI app, routers, schemas
│   ├── main.py          # App factory, lifespan, middleware
│   ├── deps.py          # Auth/DB dependencies
│   ├── routers/         # health, inbound, admin
│   └── schemas/         # Pydantic request/response models
├── worker/          # Celery worker config + tasks
│   ├── celery_app.py    # Celery bootstrap with task discovery
│   ├── tasks/           # Event handlers per domain
│   └── handlers/        # Shared business logic helpers
├── ingestion/       # Placeholder — Phase 1
├── extraction/      # Placeholder — Phase 3
└── matching/        # Placeholder — Phase 4
migrations/          # Alembic revisions
tests/               # pytest suite
```

## Configuration

All configuration via environment variables (see `.env.example`). The app uses
`pydantic-settings` to load and validate config at startup. Secrets should be
injected via environment variables in production, never committed.
