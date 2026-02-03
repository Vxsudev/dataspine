# dataspine — institutional data operations spine

A robust data operations framework for institutional-grade data pipelines.

## Features

- **Multi-source data ingestion** with pluggable adapters
- **Data normalization** and validation
- **Reconciliation** and anomaly detection
- **Audit trail** for compliance
- **Scheduled** and backfill modes

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Dataspine
```

2. Copy environment configuration:
```bash
cp config/.env.example .env
```

3. Update `.env` with your configuration values.

### Development

Start the development environment:
```bash
make dev
```

Stop the environment:
```bash
make down
```

### Testing

Run the test suite:
```bash
make test
```

Run linter:
```bash
make lint
```

### Running the Pipeline

Using Docker Compose:
```bash
docker-compose -f infra/docker-compose.yml up
```

Or directly with Python:
```bash
python scripts/run_pipeline.py --mode live --dry-run
```

For backfill mode:
```bash
python scripts/run_pipeline.py --mode backfill --start 2024-01-01 --end 2024-01-31 --client CLIENT_ID
```

## Project Structure

```
dataspine/
├── src/dataspine/          # Core application code
│   ├── adapters/           # Data source adapters
│   ├── schemas/            # Data schemas
│   ├── normalization/      # Data transformation
│   ├── validation/         # Data validation
│   ├── scheduling/         # Job scheduling
│   ├── detection/          # Anomaly detection
│   ├── reconciliation/     # Data reconciliation
│   └── audit/              # Audit logging
├── scripts/                # Utility scripts
├── tests/                  # Test suite
├── infra/                  # Infrastructure (Docker)
├── config/                 # Configuration files
└── docs/                   # Data contracts & documentation
```

## Documentation

Comprehensive data contract documentation is available in the [`docs/`](docs/) directory:

- **[Source Registry](docs/source_registry.md)** - External data sources (APIs, feeds)
- **[Canonical Schemas](docs/canonical_schemas.md)** - Normalized data schemas
- **[Data Contracts](docs/contracts.md)** - Validation rules
- **[System Invariants](docs/invariants.md)** - System-wide guarantees

## Configuration

Required environment variables:

- `DB_HOST` - Database host
- `DB_PORT` - Database port
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASS` - Database password
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `APP_ENV` - Application environment (development, staging, production)

## License

Proprietary
