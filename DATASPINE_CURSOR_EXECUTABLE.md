# DATASPINE — CURSOR EXECUTABLE PHASES
## Every Step: Cursor Prompt → Model → Verify → Auto-Commit

---

## **CRITICAL: DO THIS FIRST (ONE-TIME SETUP)**

```bash
# 1. Create project
mkdir dataspine && cd dataspine
git init

# 2. Create scripts directory
mkdir -p scripts

# 3. Copy the three scripts into scripts/
#    - scripts/smoketest.sh
#    - scripts/pre-commit-hook.sh  
#    - scripts/setup-hooks.sh

# 4. Install pre-commit hook
bash scripts/setup-hooks.sh

# 5. Verify hook is active
cat .git/hooks/pre-commit
```

**From now on:** Every `git commit` runs smoke test. If it fails, commit is blocked.

---

## **COMMIT COMMAND (SAME FOR EVERY STEP)**

```bash
git add .
git commit -m "<your message here>"
# Smoke test runs automatically
# Commit only proceeds if all tests pass
# No manual testing required — the hook handles it
```

---

## **MODEL SELECTION GUIDE**

| Model | Use For |
|---|---|
| **Claude Sonnet 4.5** | Boilerplate, structure, configs, standard patterns |
| **Claude Opus 4.5** | Domain logic, validation rules, complex algorithms |
| **Extended Thinking** | Architecture decisions, schema design, reasoning |

---
---

# PHASE 0 — ENVIRONMENT GROUND

---

## **P0.1 — Project Scaffold**

**Cursor Prompt:**
```
Create the full dataspine project structure:

src/
  dataspine/
    __init__.py              # exports __version__ = "0.1.0"
    config.py                # load_config() reads .env, raises SystemExit on missing required vars
    logging_config.py        # setup_logging(level) - structured JSON logging
    schemas/
      __init__.py
      market_data.py         # placeholder comment: "# Phase 1"
      trade_data.py          # placeholder comment: "# Phase 1"
    adapters/
      __init__.py
      base.py                # placeholder comment: "# Phase 2"
    normalization/
      __init__.py
      normalizer.py          # placeholder
      mappings.py            # placeholder
    validation/
      __init__.py
      contracts.py           # placeholder
      invariants.py          # placeholder
    scheduling/
      __init__.py
    detection/
      __init__.py
    reconciliation/
      __init__.py
    audit/
      __init__.py

scripts/
  run_pipeline.py            # argparse: --mode (live/backfill), --client, --dry-run, --start, --end
                             # stub: prints what would run, exits 0

tests/
  __init__.py
  conftest.py                # pytest setup, add src/ to path
  fixtures/
    .gitkeep

infra/
  docker-compose.yml         # network: dataspine, services: dataspine-db (postgres), dataspine-app
  Dockerfile                 # python 3.11 slim, install requirements, copy src/ and scripts/

config/
  .env.example               # DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, LOG_LEVEL, APP_ENV

.github/
  workflows/
    ci.yml                   # on push/PR: lint (ruff) + pytest

Makefile                     # targets: dev, down, test, smoke, build, lint
requirements.txt             # fastapi, uvicorn, psycopg2-binary, pydantic>=2.0, python-dotenv, pytest, apscheduler, ruff
pyproject.toml               # project name/version, pytest config, ruff config
.gitignore                   # Python defaults + .env + logs/
README.md                    # "dataspine — institutional data operations spine"

All placeholder files should be valid Python (empty or with # comments).
Config and logging should be fully functional.
Docker compose should define "dataspine" network.
```

**Model:** Claude Sonnet 4.5

**Verify:**
```bash
# Check structure exists
ls src/dataspine/schemas/
ls src/dataspine/adapters/
ls infra/
ls scripts/

# Check Python files are valid
python -m py_compile src/dataspine/__init__.py
python -m py_compile src/dataspine/config.py
python -m py_compile src/dataspine/logging_config.py

# Check run_pipeline works
export PYTHONPATH=src
python scripts/run_pipeline.py --mode live --dry-run
python scripts/run_pipeline.py --mode backfill --start 2025-01-01 --end 2025-01-02 --dry-run
```

**Commit:**
```bash
git add .
git commit -m "P0.1: full project scaffold"
# Smoke test auto-runs, commit proceeds if all pass
```

---

## **P0.2 — Local Environment Setup**

**Manual Steps:**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install package in editable mode
pip install -e .

# Copy env template
cp config/.env.example .env

# Verify lint works
make lint

# Verify tests run (0 tests OK)
make test

# Run smoke test manually
make smoke
```

**No commit needed** — this is local setup only.

---

## **P0.3 — Docker Verification**

**Manual Steps:**
```bash
# Build and start containers
make dev

# Verify postgres is reachable
docker exec dataspine-db psql -U dataspine_user -d dataspine -c "SELECT 1;"

# Check logs
docker compose -f infra/docker-compose.yml logs

# Stop (but don't remove volumes)
make down
```

**No commit needed** — infrastructure verification only.

---
---

# PHASE 1 — SCHEMAS & CONTRACTS

---

## **P1.1 — Manual Contract Definition**

**Tool:** You (text editor)

**Create:** `docs/source_registry.md`

**Content Template:**
```markdown
# SOURCE REGISTRY

## Market Data Sources
1. Source: IEX Cloud
   - Endpoint: /stock/{symbol}/quote
   - Fields: symbol, latestPrice, latestUpdate, volume, high, low, open, close
   - Expected frequency: 15min delayed

2. Source: Polygon.io
   - Endpoint: /v2/aggs/ticker/{ticker}/range/1/day/{from}/{to}
   - Fields: ticker, timestamp, open, high, low, close, volume
   - Expected frequency: daily

## Trade Data Sources  
1. Source: Execution Feed (CSV)
   - Fields: trade_id, client_id, symbol, side, quantity, price, timestamp, venue
   - Expected frequency: real-time

(Add actual sources as you define them)
```

**Create:** `docs/canonical_schemas.md`

**Content Template:**
```markdown
# CANONICAL SCHEMAS

## MarketData Schema
- symbol: str (required, uppercase, len 1-10)
- price: Decimal (required, > 0)
- timestamp: datetime (required, timezone-aware UTC)
- volume: int (required, >= 0)
- source: str (required)

## TradeData Schema
- trade_id: str (required, unique)
- client_id: str (required)
- symbol: str (required, uppercase)
- side: Literal["BUY", "SELL"] (required)
- quantity: Decimal (required, > 0)
- price: Decimal (required, > 0)
- timestamp: datetime (required, timezone-aware UTC)
- venue: str (required)

(Refine as needed)
```

**Create:** `docs/contracts.md`

**Content Template:**
```markdown
# DATA CONTRACTS

## Contract 1: Required Fields
All market data MUST have: symbol, price, timestamp, volume, source
All trade data MUST have: trade_id, client_id, symbol, side, quantity, price, timestamp, venue

## Contract 2: Price Validity
- price > 0
- price is numeric (Decimal type)

## Contract 3: Timestamp Validity  
- timestamp is timezone-aware (UTC)
- timestamp is not in the future (with 5min tolerance)

## Contract 4: Symbol Format
- uppercase only
- length 1-10 characters
- alphanumeric only

(Add domain-specific contracts)
```

**Create:** `docs/invariants.md`

**Content Template:**
```markdown
# SYSTEM INVARIANTS

1. **Idempotency**: Same input twice = same output twice
2. **Ordering**: Timestamps monotonically increase within a batch
3. **Completeness**: No partial records (all-or-nothing)
4. **Uniqueness**: trade_id unique within client_id
5. **Referential Integrity**: All symbols in trades exist in market data feed

(Add as you discover them)
```

**No commit yet** — these are inputs for next steps.

---

## **P1.2 — Pydantic Schemas**

**Cursor Prompt:**
```
Implement Pydantic v2 schemas based on docs/canonical_schemas.md:

File: src/dataspine/schemas/market_data.py
- MarketData class inheriting from BaseModel
- Fields: symbol (str, uppercase validator), price (Decimal, positive validator), timestamp (datetime, timezone-aware validator), volume (int, >= 0), source (str)
- Custom validators for uppercase symbol, positive price, future timestamp check (allow 5min tolerance)
- Example instance in docstring

File: src/dataspine/schemas/trade_data.py
- TradeData class inheriting from BaseModel  
- Fields: trade_id (str), client_id (str), symbol (str, uppercase validator), side (Literal["BUY", "SELL"]), quantity (Decimal, positive), price (Decimal, positive), timestamp (datetime, timezone-aware), venue (str)
- Same validators as MarketData where applicable
- Example instance in docstring

Use Pydantic v2 syntax (model_validator decorator).
Add clear error messages on validation failures.
```

**Model:** Claude Opus 4.5

**Verify:**
```bash
# Import schemas
python -c "from dataspine.schemas.market_data import MarketData"
python -c "from dataspine.schemas.trade_data import TradeData"

# Test basic instantiation
python -c "
from dataspine.schemas.market_data import MarketData
from decimal import Decimal
from datetime import datetime, timezone

m = MarketData(
    symbol='AAPL',
    price=Decimal('150.25'),
    timestamp=datetime.now(timezone.utc),
    volume=1000000,
    source='test'
)
print('MarketData OK:', m.symbol)
"

# Test validation (this should fail)
python -c "
from dataspine.schemas.market_data import MarketData
from decimal import Decimal
from datetime import datetime, timezone

try:
    m = MarketData(
        symbol='aapl',  # lowercase - should fail
        price=Decimal('150.25'),
        timestamp=datetime.now(timezone.utc),
        volume=1000000,
        source='test'
    )
    print('VALIDATION FAILED TO CATCH ERROR')
except Exception as e:
    print('Validation working:', type(e).__name__)
"
```

**Commit:**
```bash
git add .
git commit -m "P1.2: Pydantic schemas with validation"
```

---

## **P1.3 — Contract Validator**

**Cursor Prompt:**
```
Implement contract validation based on docs/contracts.md:

File: src/dataspine/validation/contracts.py
- ContractValidator class
- validate_market_data(data: MarketData) -> tuple[bool, list[str]]
  - Checks all contracts from docs/contracts.md
  - Returns (True, []) if valid
  - Returns (False, ["error1", "error2"]) if invalid
- validate_trade_data(data: TradeData) -> tuple[bool, list[str]]
  - Same pattern
- Each error message should be structured: "{contract_name}: {specific_violation}"
- Example: "PRICE_VALIDITY: price must be positive, got -10.5"

File: src/dataspine/validation/invariants.py
- Functions for each invariant in docs/invariants.md
- check_idempotency(batch1, batch2) -> bool
- check_monotonic_timestamps(batch) -> bool  
- check_completeness(batch) -> bool
- check_uniqueness(trades, key="trade_id") -> bool
- Each returns True if invariant holds, False otherwise
- Add logging on failure
```

**Model:** Claude Opus 4.5

**Verify:**
```bash
# Import modules
python -c "from dataspine.validation.contracts import ContractValidator"
python -c "from dataspine.validation import invariants"

# Test contract validation
python -c "
from dataspine.schemas.market_data import MarketData
from dataspine.validation.contracts import ContractValidator
from decimal import Decimal
from datetime import datetime, timezone

validator = ContractValidator()
m = MarketData(
    symbol='AAPL',
    price=Decimal('150.25'),
    timestamp=datetime.now(timezone.utc),
    volume=1000000,
    source='test'
)

valid, errors = validator.validate_market_data(m)
print('Valid:', valid, '| Errors:', errors)
assert valid == True
"
```

**Commit:**
```bash
git add .
git commit -m "P1.3: contract validator and invariant checks"
```

---

## **P1.4 — Contract Tests**

**Cursor Prompt:**
```
Create tests for schemas and contracts:

File: tests/test_schemas.py
- test_market_data_valid() — valid instance creation
- test_market_data_invalid_symbol() — lowercase symbol fails
- test_market_data_invalid_price() — negative price fails
- test_market_data_invalid_timestamp() — future timestamp fails
- Same for TradeData

File: tests/test_contracts.py
- test_contract_validator_market_valid()
- test_contract_validator_market_invalid_price()
- test_contract_validator_trade_valid()
- test_invariants_idempotency()
- test_invariants_monotonic()

Use pytest. Use fixtures from conftest if needed.
All tests should pass.
```

**Model:** Claude Sonnet 4.5

**Verify:**
```bash
# Run schema tests
python -m pytest tests/test_schemas.py -v

# Run contract tests  
python -m pytest tests/test_contracts.py -v

# Run all tests
make test
```

**Commit:**
```bash
git add .
git commit -m "P1.4: schema and contract tests"
```

---
---

# PHASE 2 — INGESTION & NORMALIZATION

---

## **P2.1 — Base Adapter**

**Cursor Prompt:**
```
Create abstract base adapter:

File: src/dataspine/adapters/base.py
- BaseAdapter abstract class
- Abstract methods:
  - fetch_raw(params: dict) -> dict  # fetch from source
  - parse_raw(raw_data: dict) -> list[dict]  # parse into dicts
  - get_source_name() -> str
- Concrete method:
  - ingest(params: dict) -> list[dict]
    - Calls fetch_raw
    - Calls parse_raw  
    - Logs input/output counts
    - Returns parsed dicts
- Use ABC and abstractmethod
- Add structured logging at each step
```

**Model:** Claude Sonnet 4.5

**Verify:**
```bash
# Import base adapter
python -c "from dataspine.adapters.base import BaseAdapter"

# Verify it's abstract (can't instantiate)
python -c "
from dataspine.adapters.base import BaseAdapter
try:
    adapter = BaseAdapter()
    print('FAIL: Should not be able to instantiate abstract class')
except TypeError:
    print('OK: BaseAdapter is abstract')
"
```

**Commit:**
```bash
git add .
git commit -m "P2.1: base adapter abstract class"
```

---

## **P2.2 — Concrete Adapters**

**Cursor Prompt:**
```
Implement market and trade adapters:

File: src/dataspine/adapters/market_adapter.py
- MarketAdapter(BaseAdapter)
- fetch_raw: For now, reads from file path in params["file_path"]
- parse_raw: Parses JSON array, extracts market data fields
- Maps source fields to canonical names (e.g., "latestPrice" -> "price")
- Logs each record parsed
- get_source_name() returns "market_feed"

File: src/dataspine/adapters/trade_adapter.py  
- TradeAdapter(BaseAdapter)
- fetch_raw: For now, reads CSV from params["file_path"]
- parse_raw: Parses CSV, maps to trade data fields
- get_source_name() returns "trade_feed"

Both should handle file not found gracefully (log error, return empty list).
```

**Model:** Claude Opus 4.5

**Verify:**
```bash
# Import adapters
python -c "from dataspine.adapters.market_adapter import MarketAdapter"
python -c "from dataspine.adapters.trade_adapter import TradeAdapter"

# Test with stub data (create small JSON file first)
python -c "
import json
with open('/tmp/test_market.json', 'w') as f:
    json.dump([{'symbol': 'AAPL', 'latestPrice': 150.25, 'latestUpdate': '2025-01-01T10:00:00Z', 'volume': 1000000}], f)
"

python -c "
from dataspine.adapters.market_adapter import MarketAdapter
adapter = MarketAdapter()
result = adapter.ingest({'file_path': '/tmp/test_market.json'})
print('Parsed:', len(result), 'records')
"
```

**Commit:**
```bash
git add .
git commit -m "P2.2: market and trade adapters"
```

---

## **P2.3 — Normalizer**

**Cursor Prompt:**
```
Create normalizer that maps to canonical schemas:

File: src/dataspine/normalization/normalizer.py
- Normalizer class
- normalize_market(raw_dict: dict) -> MarketData
  - Maps fields using mappings from mappings.py
  - Handles missing fields (log warning, skip or use default)
  - Returns MarketData instance
- normalize_trade(raw_dict: dict) -> TradeData
  - Same pattern
- normalize_batch(raw_list: list[dict], data_type: str) -> list[MarketData | TradeData]
  - Calls appropriate normalizer for each record
  - Logs success/failure count
  - Continues on error (doesn't crash entire batch)

File: src/dataspine/normalization/mappings.py
- MARKET_FIELD_MAPPINGS: dict mapping source field names to canonical names
  Example: {"latestPrice": "price", "latestUpdate": "timestamp", ...}
- TRADE_FIELD_MAPPINGS: same pattern
- TYPE_CONVERTERS: functions for type conversion (e.g., string to Decimal)
```

**Model:** Claude Opus 4.5

**Verify:**
```bash
# Import normalizer
python -c "from dataspine.normalization.normalizer import Normalizer"
python -c "from dataspine.normalization.mappings import MARKET_FIELD_MAPPINGS"

# Test normalization
python -c "
from dataspine.normalization.normalizer import Normalizer
from datetime import datetime, timezone

normalizer = Normalizer()
raw = {
    'symbol': 'AAPL',
    'latestPrice': '150.25',
    'latestUpdate': '2025-01-01T10:00:00+00:00',
    'volume': 1000000,
    'source': 'test'
}

normalized = normalizer.normalize_market(raw)
print('Normalized:', normalized.symbol, normalized.price)
"
```

**Commit:**
```bash
git add .
git commit -m "P2.3: normalizer with field mappings"
```

---

## **P2.4 — Test Fixtures & Integration**

**Cursor Prompt:**
```
Create test fixtures and wire everything together:

File: tests/fixtures/market_valid.json
- Array of 3 valid market data records (realistic data)

File: tests/fixtures/market_invalid.json  
- Array of 3 invalid records (missing fields, bad types, etc.)

File: tests/fixtures/trade_valid.csv
- 3 valid trade records

File: tests/test_adapters.py
- test_market_adapter_valid_file()
- test_market_adapter_invalid_file()
- test_trade_adapter_valid_file()

File: tests/test_normalizer.py
- test_normalize_market_valid()
- test_normalize_market_missing_field()
- test_normalize_batch()

Update: scripts/run_pipeline.py
- Wire adapters: MarketAdapter().ingest() -> Normalizer().normalize_batch() -> ContractValidator().validate_*()
- Print results (count valid, count invalid, errors)
- Still use --dry-run to test without side effects
```

**Model:** Claude Sonnet 4.5

**Verify:**
```bash
# Run adapter tests
python -m pytest tests/test_adapters.py -v

# Run normalizer tests
python -m pytest tests/test_normalizer.py -v

# Test end-to-end with run_pipeline
python scripts/run_pipeline.py --mode live --dry-run
```

**Commit:**
```bash
git add .
git commit -m "P2.4: test fixtures and pipeline integration"
```

---
---

# PHASE 3 — AUTOMATION & SCHEDULING

---

## **P3.1 — Pipeline Scheduler**

**Cursor Prompt:**
```
Create scheduling layer using APScheduler:

File: src/dataspine/scheduling/scheduler.py
- PipelineScheduler class
- __init__ takes a pipeline_fn (callable) and config (dict with schedule)
- add_job(job_id: str, cron: str) — adds scheduled job
- start() — starts the scheduler
- stop() — gracefully stops scheduler
- Uses BackgroundScheduler from apscheduler
- Logs each job execution (start, end, duration, success/failure)
- On job failure: log exception, don't crash scheduler
```

**Model:** Claude Opus 4.5

**Verify:**
```bash
# Import scheduler
python -c "from dataspine.scheduling.scheduler import PipelineScheduler"

# Test basic instantiation
python -c "
from dataspine.scheduling.scheduler import PipelineScheduler

def dummy_pipeline():
    print('Pipeline executed')
    return True

scheduler = PipelineScheduler(pipeline_fn=dummy_pipeline, config={})
print('Scheduler created')
"
```

**Commit:**
```bash
git add .
git commit -m "P3.1: pipeline scheduler with APScheduler"
```

---

## **P3.2 — Retry Handler**

**Cursor Prompt:**
```
Create retry logic with exponential backoff:

File: src/dataspine/scheduling/retry.py
- RetryHandler class
- execute_with_retry(fn: callable, *args, max_retries=3, base_delay=1.0, **kwargs)
  - Calls fn with args/kwargs
  - On failure: exponential backoff (base_delay * 2^attempt)
  - Logs each retry attempt
  - After max_retries: marks as dead letter, logs final failure
  - Returns tuple: (success: bool, result: any, attempts: int)
- Distinguish transient errors (network, timeout) from permanent errors (validation)
- For permanent errors: no retry, immediate dead letter
```

**Model:** Claude Opus 4.5

**Verify:**
```bash
# Import retry handler
python -c "from dataspine.scheduling.retry import RetryHandler"

# Test retry logic
python -c "
from dataspine.scheduling.retry import RetryHandler
import time

attempts = 0

def flaky_fn():
    global attempts
    attempts += 1
    if attempts < 3:
        raise Exception('Transient failure')
    return 'Success'

handler = RetryHandler()
success, result, count = handler.execute_with_retry(flaky_fn, max_retries=5)
print('Success:', success, '| Attempts:', count, '| Result:', result)
assert success == True
assert count == 3
"
```

**Commit:**
```bash
git add .
git commit -m "P3.2: retry handler with exponential backoff"
```

---

## **P3.3 — Backfill Runner**

**Cursor Prompt:**
```
Create deterministic backfill logic:

File: src/dataspine/scheduling/backfill.py
- BackfillRunner class
- run_backfill(start_date: str, end_date: str, pipeline_fn: callable) -> dict
  - Iterates from start_date to end_date (inclusive)
  - For each date: calls pipeline_fn with date param
  - Logs each date processed
  - Returns summary: {dates_processed: int, dates_failed: int, total_duration: float}
- Deterministic: same date range = same order = same results
- Uses retry handler for each date
- On failure: logs date, continues to next (don't halt backfill)
```

**Model:** Claude Opus 4.5

**Verify:**
```bash
# Import backfill runner
python -c "from dataspine.scheduling.backfill import BackfillRunner"

# Test backfill
python -c "
from dataspine.scheduling.backfill import BackfillRunner

def dummy_pipeline(date):
    print(f'Processing {date}')
    return True

runner = BackfillRunner()
result = runner.run_backfill('2025-01-01', '2025-01-03', dummy_pipeline)
print('Backfill result:', result)
assert result['dates_processed'] == 3
"

# Test determinism (run twice, compare)
python -c "
from dataspine.scheduling.backfill import BackfillRunner

results = []
def pipeline(date):
    return date

runner = BackfillRunner()
results.append(runner.run_backfill('2025-01-01', '2025-01-05', pipeline))
results.append(runner.run_backfill('2025-01-01', '2025-01-05', pipeline))

assert results[0] == results[1], 'Backfill not deterministic'
print('Determinism verified')
"
```

**Commit:**
```bash
git add .
git commit -m "P3.3: deterministic backfill runner"
```

---

## **P3.4 — Wire into run_pipeline**

**Cursor Prompt:**
```
Update run_pipeline.py to use scheduler and backfill:

- If --mode live: use PipelineScheduler with cron from config
- If --mode backfill: use BackfillRunner with --start and --end dates
- Pipeline function: adapters -> normalizer -> validator (from Phase 2)
- Add --schedule arg for live mode (default: "*/15 * * * *" = every 15 min)
- Logs all execution details
- On SIGINT (Ctrl+C): gracefully stop scheduler
```

**Model:** Claude Opus 4.5

**Verify:**
```bash
# Test live mode (dry-run)
python scripts/run_pipeline.py --mode live --dry-run --schedule "*/5 * * * *"

# Test backfill mode
python scripts/run_pipeline.py --mode backfill --start 2025-01-01 --end 2025-01-05 --dry-run

# Test that run_pipeline works as CLI
python scripts/run_pipeline.py --help
```

**Commit:**
```bash
git add .
git commit -m "P3.4: wire scheduler and backfill into run_pipeline"
```

---

## **P3.5 — Automation Tests**

**Cursor Prompt:**
```
Create tests for scheduling components:

File: tests/test_scheduler.py
- test_scheduler_add_job()
- test_scheduler_start_stop()
- test_scheduler_job_failure_doesnt_crash()

File: tests/test_retry.py
- test_retry_success_first_attempt()
- test_retry_success_after_retries()
- test_retry_max_retries_exceeded()
- test_retry_permanent_error_no_retry()

File: tests/test_backfill.py
- test_backfill_date_range()
- test_backfill_determinism() — run twice, assert same results
- test_backfill_failure_continues()

Use mocks where appropriate (don't actually sleep during tests).
```

**Model:** Claude Sonnet 4.5

**Verify:**
```bash
# Run all automation tests
python -m pytest tests/test_scheduler.py tests/test_retry.py tests/test_backfill.py -v

# Run all tests
make test
```

**Commit:**
```bash
git add .
git commit -m "P3.5: automation and scheduling tests"
```

---
---

# PHASE 4 — ANOMALY DETECTION

---

## **P4.1 — Manual Detection Rule Registry**

**Tool:** You (text editor)

**Create:** `docs/detection_rules.md`

**Content Template:**
```markdown
# ANOMALY DETECTION RULES

## Rule 1: Missing Data
**Detector:** MissingDataDetector
**Trigger:** No data received within expected window
**Threshold:** 2x expected interval (e.g., if data comes every 15min, alert after 30min)
**Alert:** "Missing data: expected data from {source} at {expected_time}, none received"

## Rule 2: Time Gap
**Detector:** TimeGapDetector  
**Trigger:** Gap between consecutive timestamps exceeds threshold
**Threshold:** 60 minutes (configurable)
**Alert:** "Time gap detected: {gap_minutes} minutes between {time1} and {time2}"

## Rule 3: Volume Shift
**Detector:** VolumeShiftDetector
**Trigger:** Volume deviates >X% from rolling average
**Threshold:** ±50% from 20-period rolling average
**Alert:** "Volume anomaly: {current_volume} vs avg {avg_volume} ({percent_change}%)"

## Rule 4: Latency Breach
**Detector:** LatencyDetector
**Trigger:** Data timestamp vs ingestion timestamp gap exceeds SLA
**Threshold:** 5 minutes
**Alert:** "Latency breach: data delayed by {delay_minutes} minutes"

(Tune thresholds based on actual data)
```

**No commit yet** — input for next step.

---

## **P4.2 — Base Detector**

**Cursor Prompt:**
```
Create abstract base detector:

File: src/dataspine/detection/base.py
- BaseDetector abstract class
- Abstract methods:
  - detect(data: list) -> list[dict]  # returns list of anomalies found
  - get_detector_name() -> str
- Each anomaly dict has: {rule: str, severity: str, message: str, context: dict, timestamp: datetime}
- Concrete method:
  - run(data: list) -> list[dict]
    - Calls detect()
    - Logs detection results (count of anomalies)
    - Returns anomaly list
- Use ABC and abstractmethod
```

**Model:** Claude Sonnet 4.5

**Verify:**
```bash
# Import base detector
python -c "from dataspine.detection.base import BaseDetector"

# Verify abstract
python -c "
from dataspine.detection.base import BaseDetector
try:
    detector = BaseDetector()
    print('FAIL: Should not instantiate')
except TypeError:
    print('OK: BaseDetector is abstract')
"
```

**Commit:**
```bash
git add .
git commit -m "P4.2: base detector abstract class"
```

---

## **P4.3 — Concrete Detectors**

**Cursor Prompt:**
```
Implement the 4 detectors from docs/detection_rules.md:

File: src/dataspine/detection/missing_data.py
- MissingDataDetector(BaseDetector)
- Checks if data exists for expected time windows
- Config: expected_interval_minutes
- Returns anomalies if gap > 2 * expected_interval

File: src/dataspine/detection/time_gap.py
- TimeGapDetector(BaseDetector)
- Checks gaps between consecutive timestamps
- Config: max_gap_minutes (default 60)
- Returns anomalies if gap > threshold

File: src/dataspine/detection/volume_shift.py
- VolumeShiftDetector(BaseDetector)
- Calculates rolling average volume (20-period window)
- Config: deviation_percent (default 50)
- Returns anomalies if current volume deviates >X% from avg

File: src/dataspine/detection/latency.py
- LatencyDetector(BaseDetector)
- Compares data timestamp vs ingestion timestamp
- Config: max_latency_minutes (default 5)
- Returns anomalies if delay > threshold

Each detector should:
- Have clear docstrings explaining logic
- Log when thresholds are breached
- Return structured anomaly dicts
- Handle empty data gracefully (return [])
```

**Model:** Claude Opus 4.5

**Verify:**
```bash
# Import all detectors
python -c "from dataspine.detection.missing_data import MissingDataDetector"
python -c "from dataspine.detection.time_gap import TimeGapDetector"
python -c "from dataspine.detection.volume_shift import VolumeShiftDetector"
python -c "from dataspine.detection.latency import LatencyDetector"

# Test time gap detector with dummy data
python -c "
from dataspine.detection.time_gap import TimeGapDetector
from datetime import datetime, timedelta, timezone

detector = TimeGapDetector(config={'max_gap_minutes': 30})

data = [
    {'timestamp': datetime.now(timezone.utc)},
    {'timestamp': datetime.now(timezone.utc) + timedelta(hours=2)},  # 2 hour gap
]

anomalies = detector.run(data)
print('Anomalies detected:', len(anomalies))
assert len(anomalies) > 0, 'Should detect gap'
"
```

**Commit:**
```bash
git add .
git commit -m "P4.3: four concrete anomaly detectors"
```

---

## **P4.4 — Alert Formatter**

**Cursor Prompt:**
```
Create alert formatter:

File: src/dataspine/detection/alert.py
- AlertFormatter class
- format_alert(anomaly: dict) -> str
  - Takes anomaly dict from detector
  - Returns human-readable formatted string
  - Includes: severity, rule name, message, timestamp, context
  - Example: "[HIGH] VOLUME_SHIFT at 2025-01-01 10:00:00 UTC: Volume anomaly detected (current: 500k, avg: 1M, -50%)"
- format_batch(anomalies: list[dict]) -> str
  - Formats multiple anomalies
  - Groups by severity
  - Returns summary + detailed list

File: src/dataspine/detection/registry.py
- DETECTOR_REGISTRY: dict mapping detector names to classes
- get_all_detectors() -> list[BaseDetector]
- run_all_detectors(data, configs) -> list[dict]
  - Runs all registered detectors
  - Aggregates all anomalies
  - Returns combined list
```

**Model:** Claude Sonnet 4.5

**Verify:**
```bash
# Import alert formatter
python -c "from dataspine.detection.alert import AlertFormatter"
python -c "from dataspine.detection.registry import DETECTOR_REGISTRY, get_all_detectors"

# Test alert formatting
python -c "
from dataspine.detection.alert import AlertFormatter
from datetime import datetime, timezone

anomaly = {
    'rule': 'VOLUME_SHIFT',
    'severity': 'HIGH',
    'message': 'Volume dropped 50%',
    'context': {'current': 500000, 'avg': 1000000},
    'timestamp': datetime.now(timezone.utc)
}

formatter = AlertFormatter()
alert_str = formatter.format_alert(anomaly)
print('Alert:', alert_str)
"

# Test registry
python -c "
from dataspine.detection.registry import get_all_detectors
detectors = get_all_detectors()
print('Registered detectors:', len(detectors))
assert len(detectors) == 4
"
```

**Commit:**
```bash
git add .
git commit -m "P4.4: alert formatter and detector registry"
```

---

## **P4.5 — Wire Detectors into Pipeline**

**Cursor Prompt:**
```
Update run_pipeline.py to include anomaly detection:

- After normalization and validation
- Run all detectors on normalized data
- Format alerts
- Log alerts (console + structured log file)
- If --alert-file provided: write alerts to file
- Continue pipeline even if anomalies detected (don't halt)
```

**Model:** Claude Sonnet 4.5

**Verify:**
```bash
# Test pipeline with detection
python scripts/run_pipeline.py --mode live --dry-run

# Check that detection runs
grep -i "anomaly" <logs or output>
```

**Commit:**
```bash
git add .
git commit -m "P4.5: wire anomaly detection into pipeline"
```

---

## **P4.6 — Detection Tests & False Positive Measurement**

**Cursor Prompt:**
```
Create comprehensive detection tests:

File: tests/test_detection.py
- test_missing_data_detector()
- test_time_gap_detector()  
- test_volume_shift_detector()
- test_latency_detector()
- test_alert_formatter()
- test_detector_registry()
- test_false_positive_rate() — runs detectors on known-good data, measures false positives

File: tests/fixtures/detection_clean.json
- Array of clean data that should NOT trigger any anomalies

File: tests/fixtures/detection_anomalous.json
- Array of data with intentional anomalies (each rule should trigger)

Target: <5% false positive rate on clean data.
```

**Model:** Claude Opus 4.5

**Verify:**
```bash
# Run detection tests
python -m pytest tests/test_detection.py -v

# Measure false positive rate
python -m pytest tests/test_detection.py::test_false_positive_rate -v

# Run all tests
make test
```

**Commit:**
```bash
git add .
git commit -m "P4.6: detection tests and false positive measurement"
```

---
---

# PHASE 5 — RECONCILIATION & REPLAY

---

## **P5.1 — Diff Report**

**Cursor Prompt:**
```
Create field-level diff reporting:

File: src/dataspine/reconciliation/diff.py
- DiffReport class
- compare_records(record1: dict, record2: dict, key_fields: list[str]) -> dict
  - Compares two records field by field
  - Returns diff dict: {field: {old: value1, new: value2}}
  - Only includes fields that differ
  - Ignores metadata fields (like _id, created_at unless specified)
- compare_batches(batch1: list[dict], batch2: list[dict], key_field: str) -> dict
  - Matches records by key_field
  - Returns: {added: [], removed: [], modified: [{key, diffs}]}
  - Logs summary stats
- generate_report(diff_result: dict) -> str
  - Formats diff_result into readable report
  - Groups by type (added/removed/modified)
  - Shows field-level changes
```

**Model:** Claude Opus 4.5

**Verify:**
```bash
# Import diff module
python -c "from dataspine.reconciliation.diff import DiffReport"

# Test record comparison
python -c "
from dataspine.reconciliation.diff import DiffReport

r1 = {'id': 1, 'symbol': 'AAPL', 'price': 150.0}
r2 = {'id': 1, 'symbol': 'AAPL', 'price': 155.0}

diff_report = DiffReport()
diffs = diff_report.compare_records(r1, r2, key_fields=['id'])
print('Diffs:', diffs)
assert 'price' in diffs
"
```

**Commit:**
```bash
git add .
git commit -m "P5.1: field-level diff reporting"
```

---

## **P5.2 — Replay Engine**

**Cursor Prompt:**
```
Create deterministic replay engine:

File: src/dataspine/reconciliation/replay.py
- ReplayEngine class
- replay_pipeline(start_date: str, end_date: str, pipeline_fn: callable, output_file: str) -> dict
  - Re-runs pipeline for date range
  - Captures all output to output_file (JSONL format: one record per line)
  - Returns summary: {dates_processed, records_generated, duration}
  - Deterministic: same inputs = same outputs = same file
- compare_replays(replay1_file: str, replay2_file: str) -> dict
  - Loads both files
  - Compares line by line
  - Returns: {matching: int, differing: int, diffs: list}
- Uses DiffReport for detailed comparison
```

**Model:** Claude Opus 4.5

**Verify:**
```bash
# Import replay engine
python -c "from dataspine.reconciliation.replay import ReplayEngine"

# Test replay (dry run)
python -c "
from dataspine.reconciliation.replay import ReplayEngine
import os

def dummy_pipeline(date):
    return [{'date': date, 'value': 100}]

engine = ReplayEngine()
result = engine.replay_pipeline('2025-01-01', '2025-01-03', dummy_pipeline, '/tmp/replay1.jsonl')
print('Replay result:', result)
assert os.path.exists('/tmp/replay1.jsonl')
"

# Test determinism
python -c "
from dataspine.reconciliation.replay import ReplayEngine

def dummy_pipeline(date):
    return [{'date': date, 'value': 100}]

engine = ReplayEngine()
engine.replay_pipeline('2025-01-01', '2025-01-03', dummy_pipeline, '/tmp/replay1.jsonl')
engine.replay_pipeline('2025-01-01', '2025-01-03', dummy_pipeline, '/tmp/replay2.jsonl')

comparison = engine.compare_replays('/tmp/replay1.jsonl', '/tmp/replay2.jsonl')
print('Comparison:', comparison)
assert comparison['differing'] == 0, 'Replays not deterministic'
"
```

**Commit:**
```bash
git add .
git commit -m "P5.2: deterministic replay engine"
```

---

## **P5.3 — Audit Log Writer**

**Cursor Prompt:**
```
Create append-only audit logging:

File: src/dataspine/audit/writer.py
- AuditLogWriter class
- __init__(log_file: str) — opens file in append mode
- log_event(event_type: str, entity_type: str, entity_id: str, old_state: dict, new_state: dict, metadata: dict)
  - Writes JSONL entry with:
    - timestamp (UTC)
    - event_type (created, updated, validated, detected_anomaly, reconciled)
    - entity_type (market_data, trade_data)
    - entity_id
    - old_state (before)
    - new_state (after)
    - metadata (user, source, etc.)
  - Appends to file (never overwrites)
  - Flushes after each write (durability)
- close() — closes file handle
- Use context manager support (with statement)
```

**Model:** Claude Opus 4.5

**Verify:**
```bash
# Import audit writer
python -c "from dataspine.audit.writer import AuditLogWriter"

# Test audit logging
python -c "
from dataspine.audit.writer import AuditLogWriter
import os

log_file = '/tmp/audit_test.jsonl'
if os.path.exists(log_file):
    os.remove(log_file)

with AuditLogWriter(log_file) as writer:
    writer.log_event(
        event_type='created',
        entity_type='market_data',
        entity_id='AAPL_2025-01-01',
        old_state={},
        new_state={'symbol': 'AAPL', 'price': 150.0},
        metadata={'source': 'test'}
    )

# Verify file exists and has content
assert os.path.exists(log_file)
with open(log_file) as f:
    lines = f.readlines()
    print('Audit entries:', len(lines))
    assert len(lines) == 1
"
```

**Commit:**
```bash
git add .
git commit -m "P5.3: append-only audit log writer"
```

---

## **P5.4 — Wire into Pipeline**

**Cursor Prompt:**
```
Update run_pipeline.py to use audit logging:

- Create AuditLogWriter at pipeline start
- Log events at key points:
  - After adapter fetch: log_event('ingested', ...)
  - After normalization: log_event('normalized', ...)
  - After validation: log_event('validated', ...) or log_event('validation_failed', ...)
  - After detection: log_event('anomaly_detected', ...)
  - After reconciliation: log_event('reconciled', ...)
- Use --audit-log arg for output file (default: logs/audit.jsonl)
- Ensure logs directory exists
```

**Model:** Claude Sonnet 4.5

**Verify:**
```bash
# Run pipeline with audit logging
mkdir -p logs
python scripts/run_pipeline.py --mode live --dry-run --audit-log logs/audit.jsonl

# Verify audit log created
ls logs/audit.jsonl

# Check content
cat logs/audit.jsonl | head -5
```

**Commit:**
```bash
git add .
git commit -m "P5.4: wire audit logging into pipeline"
```

---

## **P5.5 — Reconciliation Tests**

**Cursor Prompt:**
```
Create tests for reconciliation and replay:

File: tests/test_diff.py
- test_compare_records_identical()
- test_compare_records_different()
- test_compare_batches()
- test_generate_report()

File: tests/test_replay.py
- test_replay_pipeline()
- test_replay_determinism() — run twice, compare outputs
- test_compare_replays()

File: tests/test_audit.py
- test_audit_log_writer()
- test_audit_log_append_only() — write multiple times, verify all entries present
- test_audit_log_context_manager()

All tests should pass and prove determinism.
```

**Model:** Claude Sonnet 4.5

**Verify:**
```bash
# Run reconciliation tests
python -m pytest tests/test_diff.py tests/test_replay.py tests/test_audit.py -v

# Run all tests
make test
```

**Commit:**
```bash
git add .
git commit -m "P5.5: reconciliation and replay tests"
```

---
---

# PHASE 6 — DEPLOYMENT & OPS

---

## **P6.1 — Production Dockerfile**

**Cursor Prompt:**
```
Create production-ready multi-stage Dockerfile:

File: infra/Dockerfile.prod
- Stage 1: Builder
  - Python 3.11 slim
  - Install build dependencies
  - Install Python packages
  - Create virtual environment
- Stage 2: Runtime
  - Python 3.11 slim
  - Copy only virtual environment from builder
  - Copy src/ and scripts/
  - Create non-root user
  - Set WORKDIR
  - Add HEALTHCHECK (curl or python check)
  - CMD runs run_pipeline.py

Minimal layers, minimal attack surface, no unnecessary packages.
```

**Model:** Claude Sonnet 4.5

**Verify:**
```bash
# Build production image
docker build -f infra/Dockerfile.prod -t dataspine:prod .

# Run image
docker run --rm dataspine:prod --help

# Check healthcheck
docker inspect dataspine:prod | grep -i health
```

**Commit:**
```bash
git add .
git commit -m "P6.1: production multi-stage Dockerfile"
```

---

## **P6.2 — Complete CI/CD Pipeline**

**Cursor Prompt:**
```
Enhance .github/workflows/ci.yml with full pipeline:

Jobs:
1. lint — ruff check src/
2. test — pytest with coverage
3. smoke — bash scripts/smoketest.sh
4. build — docker build (both dev and prod Dockerfiles)
5. security — run safety check on dependencies (optional)

Run on: push to main, pull requests
Fail fast: if any job fails, stop pipeline
Cache: pip dependencies
Artifacts: coverage reports, test results
```

**Model:** Claude Sonnet 4.5

**Verify:**
```bash
# Trigger CI locally (if using act or similar)
# Otherwise push to GitHub and verify CI runs

# Check CI config is valid
cat .github/workflows/ci.yml
```

**Commit:**
```bash
git add .
git commit -m "P6.2: complete CI/CD pipeline with coverage"
```

---

## **P6.3 — Runbooks**

**Tool:** You (text editor)

**Create:** `docs/runbooks/ingestion.md`

```markdown
# INGESTION RUNBOOK

## Starting the Pipeline
```bash
python scripts/run_pipeline.py --mode live --schedule "*/15 * * * *"
```

## Health Check
```bash
# Check logs
tail -f logs/pipeline.log

# Check audit log
tail -f logs/audit.jsonl

# Check postgres
docker exec dataspine-db psql -U dataspine_user -d dataspine -c "SELECT COUNT(*) FROM market_data;"
```

## Failure Handling
- **Validation failure**: Check audit log for specific errors, fix data source
- **Adapter failure**: Check network/file access, verify source availability
- **Dead letter queue**: Review logs/dead_letters/, investigate permanent failures
```

**Create:** `docs/runbooks/anomaly_detection.md`

```markdown
# ANOMALY DETECTION RUNBOOK

## Reviewing Anomalies
```bash
# Check detection output
cat logs/anomalies.log | jq '.severity' | sort | uniq -c

# Filter by rule
cat logs/anomalies.log | jq 'select(.rule == "VOLUME_SHIFT")'
```

## Tuning Thresholds
Edit `docs/detection_rules.md` and update detector configs.

## False Positives
Run: `python -m pytest tests/test_detection.py::test_false_positive_rate -v`
Target: <5%
```

**Create:** `docs/runbooks/reconciliation.md`

```markdown
# RECONCILIATION RUNBOOK

## Running Replay
```bash
# Replay specific date range
python -c "from dataspine.reconciliation.replay import ReplayEngine; ..."
```

## Comparing Outputs
```bash
# Run diff report
python -c "from dataspine.reconciliation.diff import DiffReport; ..."
```

## Investigating Discrepancies
Check audit log for entity_id, review state changes.
```

**No commit yet** — will commit all runbooks together.

---

## **P6.4 — Production Readiness Checklist**

**Tool:** You (text editor)

**Create:** `docs/PRODUCTION_READINESS.md`

```markdown
# PRODUCTION READINESS CHECKLIST

## Code Quality
- [ ] All tests passing
- [ ] Coverage >80%
- [ ] Lint passes (ruff)
- [ ] Smoke test passes
- [ ] No TODO/FIXME in production code

## Operations
- [ ] Docker builds successfully
- [ ] Healthcheck endpoint works
- [ ] Logs are structured JSON
- [ ] Audit log is append-only
- [ ] Error handling on all adapters

## Documentation
- [ ] Runbooks exist for each subsystem
- [ ] Schemas documented
- [ ] Contracts documented
- [ ] Detection rules documented
- [ ] README updated

## Security
- [ ] No secrets in code
- [ ] .env.example doesn't contain real credentials
- [ ] Docker runs as non-root user
- [ ] Dependencies scanned (safety)

## Deployment
- [ ] CI/CD pipeline configured
- [ ] Docker images tagged properly
- [ ] Database migrations tested
- [ ] Rollback plan exists

## Monitoring
- [ ] Logs centralized
- [ ] Anomaly alerts routed
- [ ] Dead letter queue monitored
- [ ] Performance metrics tracked
```

**Commit:**
```bash
git add docs/runbooks/ docs/PRODUCTION_READINESS.md
git commit -m "P6.3-P6.4: runbooks and production readiness checklist"
```

---

## **P6.5 — Final Integration Test**

**Cursor Prompt:**
```
Create end-to-end integration test:

File: tests/test_integration_e2e.py
- test_full_pipeline_live_mode()
  - Starts pipeline in live mode (dry-run)
  - Feeds test data through all stages
  - Verifies: ingestion -> normalization -> validation -> detection -> audit log
  - Asserts: correct record counts, no crashes, audit log has entries
- test_full_pipeline_backfill_mode()
  - Runs backfill for 5 dates
  - Verifies determinism (run twice, compare)
  - Asserts: all dates processed, replay produces identical results

Use Docker Compose to spin up postgres for test.
Clean up after test.
```

**Model:** Claude Opus 4.5

**Verify:**
```bash
# Run integration test
python -m pytest tests/test_integration_e2e.py -v -s

# Verify it uses Docker
docker ps  # Should show postgres running during test

# Run all tests one final time
make test
make smoke
```

**Commit:**
```bash
git add .
git commit -m "P6.5: end-to-end integration test"
```

---

## **P6.6 — Demo Package Assembly**

**Tool:** You (manual)

**Assemble:**
1. Blueprint diagram (architecture diagram showing data flow)
2. Source registry (docs/source_registry.md)
3. Schema contracts (docs/canonical_schemas.md + docs/contracts.md)
4. Detection rules (docs/detection_rules.md)
5. Pipeline execution recording (terminal recording or log excerpt)
6. Anomaly detection output (logs/anomalies.log sample)
7. Reconciliation proof (replay comparison showing 100% determinism)
8. One-page summary (executive summary of system capabilities)

**Create:** `docs/DEMO_PACKAGE.md`

```markdown
# DATASPINE DEMO PACKAGE

## 1. System Architecture
[Insert or link to architecture diagram]

## 2. Data Sources & Contracts
- See: docs/source_registry.md
- See: docs/canonical_schemas.md
- See: docs/contracts.md

## 3. Automation & Reliability
- Pipeline runs unattended (via scheduler)
- Retry logic with exponential backoff
- Backfill is deterministic (proven via replay tests)

## 4. Anomaly Detection
- 4 detection rules (missing data, time gap, volume shift, latency)
- <5% false positive rate (measured in tests)
- Alerts are contextual and actionable

## 5. Reconciliation & Audit
- Field-level diff reporting
- 100% deterministic replay (proven)
- Append-only audit log for full traceability

## 6. Production Readiness
- Docker containerized
- CI/CD automated
- Runbooks for each subsystem
- Healthchecks and structured logging

## 7. Key Metrics
- Data latency: <SLA threshold
- Anomaly false positives: <5%
- Backfill determinism: 100%
- Test coverage: >80%

---

**One-Line Summary:**
Built a production data operations backbone for multi-source market and trade data, automating ingestion, normalization, anomaly detection, and reconciliation — directly addressing operational risk in systematic investment workflows.
```

**Verify:**
- Review all docs for completeness
- Ensure all links work
- Check that demo artifacts exist

**Commit:**
```bash
git add docs/DEMO_PACKAGE.md
git commit -m "P6.6: demo package assembled"
```

---
---

# FINAL STEP — TAG RELEASE

```bash
# Tag version
git tag -a v1.0.0 -m "dataspine v1.0.0 — production ready"

# Push everything
git push origin main --tags

# Celebrate 🎉
```

---
---

# SUMMARY OF WORKFLOW

1. **Every phase has discrete steps**
2. **Every step has: Cursor prompt, model choice, verification commands, automatic commit**
3. **Smoke test auto-runs on every commit** — blocks commit if anything fails
4. **No manual testing required** — the pre-commit hook enforces quality
5. **Linear progression** — can't commit Phase 2 until Phase 1 passes
6. **Determinism proven by tests** — backfill and replay tests verify repeatability

**Result:** A production-grade institutional DataOps spine, built systematically, tested comprehensively, ready to demonstrate operational excellence.

---

**END OF EXECUTABLE PLAN**
