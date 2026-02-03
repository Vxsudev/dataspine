# DATA CONTRACTS

Data contracts are validation rules that MUST be enforced on all data after normalization.

## Contract 1: Required Fields

**Market Data Requirements**:
All MarketData instances MUST have:
- `symbol` (non-null)
- `price` (non-null)
- `timestamp` (non-null)
- `volume` (non-null)
- `source` (non-null)

**Trade Data Requirements**:
All TradeData instances MUST have:
- `trade_id` (non-null)
- `client_id` (non-null)
- `symbol` (non-null)
- `side` (non-null)
- `quantity` (non-null)
- `price` (non-null)
- `timestamp` (non-null)
- `venue` (non-null)

**Violation**: Record is rejected with error "REQUIRED_FIELDS: Missing required field {field_name}"

## Contract 2: Price Validity

**Rules**:
- `price` field MUST be > 0
- `price` field MUST be numeric (Decimal type)
- `price` field MUST have <= 4 decimal places
- `quantity` field (for trades) MUST follow same rules

**Violation**: Record is rejected with error "PRICE_VALIDITY: price must be positive, got {value}"

## Contract 3: Timestamp Validity

**Rules**:
- `timestamp` MUST be timezone-aware
- `timestamp` MUST use UTC timezone
- `timestamp` MUST NOT be more than 5 minutes in the future (clock skew tolerance)
- `timestamp` MUST NOT be before year 2000 (sanity check)

**Violation**: Record is rejected with appropriate error:
- "TIMESTAMP_VALIDITY: timestamp must be timezone-aware"
- "TIMESTAMP_VALIDITY: timestamp must be in UTC"
- "TIMESTAMP_VALIDITY: timestamp cannot be >5min in future, got {value}"

## Contract 4: Symbol Format

**Rules**:
- `symbol` MUST be uppercase only (A-Z, 0-9, period allowed)
- `symbol` MUST be 1-10 characters long
- `symbol` MUST be alphanumeric (plus period for class shares)
- No whitespace allowed

**Violation**: Record is rejected with error "SYMBOL_FORMAT: {specific_violation}"

## Contract 5: Trade-Specific Rules

**Rules**:
- `side` MUST be exactly "BUY" or "SELL" (no case variations)
- `quantity` MUST be > 0
- `trade_id` MUST be unique within a client_id
- `venue` MUST be non-empty string

**Violation**: Record is rejected with error describing the specific violation
