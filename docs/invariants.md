# SYSTEM INVARIANTS

System invariants are properties that MUST hold true across batches and operations.

## Invariant 1: Idempotency

**Definition**: Processing the same input data twice must produce identical output.

**Rules**:
- Same raw data input → same normalized output
- Same normalized data → same validation results
- Same batch → same anomaly detection results

**Test**: Run pipeline twice on identical input, compare outputs byte-for-byte

**Violation Impact**: Non-deterministic behavior, unreliable backfills, inability to replay

## Invariant 2: Timestamp Ordering

**Definition**: Within a batch, timestamps must be monotonically increasing or equal.

**Rules**:
- For batch[i] and batch[i+1]: timestamp[i] <= timestamp[i+1]
- Ties (equal timestamps) are allowed
- This applies after sorting if source is unordered

**Test**: Sort batch by timestamp, verify no timestamp is less than its predecessor

**Violation Impact**: Incorrect time-series analysis, wrong anomaly detection

## Invariant 3: Batch Completeness

**Definition**: Batches are atomic - all records succeed or all fail together.

**Rules**:
- Cannot commit partial batch to storage
- If any record in batch fails validation, entire batch is rejected
- OR: All invalid records moved to dead letter queue, valid records processed

**Test**: Submit batch with 1 invalid record, verify either entire batch rejected or DLQ used

**Violation Impact**: Inconsistent data state, broken referential integrity

## Invariant 4: Uniqueness

**Definition**: Certain fields must be unique within their scope.

**Rules**:
- `trade_id` must be unique within `client_id` scope
- No duplicate trades from same client
- Market data can have duplicate symbols (different timestamps)

**Test**: Submit batch with duplicate trade_id for same client_id, verify rejection

**Violation Impact**: Double-counting trades, incorrect position calculations

## Invariant 5: Referential Integrity

**Definition**: Trade symbols must exist in market data universe.

**Rules**:
- Before accepting trade for symbol X, verify market data exists for X
- Warning (not error) if symbol not found - may be new listing
- Log symbols without market data for investigation

**Test**: Submit trade for non-existent symbol, verify warning logged

**Violation Impact**: Trades on unknown symbols, pricing data gaps
