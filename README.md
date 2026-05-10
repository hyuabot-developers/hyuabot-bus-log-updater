# hyuabot-bus-log-updater

A daily job that fetches historical bus departure data from the public API and records it in the HYUabot database. Runs every day at 01:00 as a Kubernetes CronJob.

## Overview

On each run the job fetches bus departure logs for a configurable number of past days and inserts them into the `bus_departure_log` table. The number of days to look back is controlled by the `DAYS_PAST` environment variable.

## Architecture

```
src/
├── main.py           # Entry point; fetches and inserts departure logs
├── models.py         # SQLAlchemy ORM models (BusDepartureLog)
└── utils/
    └── database.py   # PostgreSQL engine factory
```

## Requirements

- Python ≥ 3.12
- PostgreSQL
- Public bus API key

## Environment Variables

| Variable            | Description                              |
|---------------------|------------------------------------------|
| `BUS_API_KEY`       | Public bus API service key               |
| `DAYS_PAST`         | Number of past days to fetch (default: 1) |
| `POSTGRES_ID`       | PostgreSQL username                      |
| `POSTGRES_PASSWORD` | PostgreSQL password                      |
| `POSTGRES_HOST`     | PostgreSQL host                          |
| `POSTGRES_PORT`     | PostgreSQL port                          |
| `POSTGRES_DB`       | PostgreSQL database name                 |

## Running Locally

```bash
pip install -e .

export BUS_API_KEY=your_api_key
export DAYS_PAST=1
export POSTGRES_ID=postgres
export POSTGRES_PASSWORD=password
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=hyuabot

cd src && python main.py
```

## Docker

The container exits after a single run — schedule it externally (Kubernetes CronJob daily at 01:00).

```bash
docker build -t hyuabot-bus-log-updater .

docker run --rm \
  -e BUS_API_KEY=your_api_key \
  -e DAYS_PAST=1 \
  -e POSTGRES_ID=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_HOST=host.docker.internal \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=hyuabot \
  hyuabot-bus-log-updater
```

## Development

```bash
pip install -e .[lint]       # flake8
pip install -e .[typecheck]  # mypy
pip install -e .[test]       # pytest
```

```bash
python -m flake8 src/ tests/
python -m mypy src/ tests/
python -m pytest -v
```

Tests run against a PostgreSQL instance at `localhost:25432`.

## CI/CD

| Workflow | Trigger | Jobs |
|---|---|---|
| `code-check.yml` | Push to any branch except `main` | lint, typecheck, test |
| `deploy.yml` | PR merged to `main` (or manual dispatch) | Docker build → push to `localhost:5000` |

CI runners: self-hosted X64 Linux (code checks) · ARM64 Linux (Docker build).

## License

GPLv3
