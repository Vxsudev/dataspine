# CANONICAL SCHEMAS

These are the normalized, validated schemas that all data must conform to after ingestion.

## MarketData Schema

**Purpose**: Normalized representation of market price and volume data from any source.

**Fields**:
- `symbol` (str, required)
  - Stock ticker symbol
  - Constraints: uppercase only, 1-10 characters, alphanumeric
  - Example: "AAPL", "MSFT", "BRK.B"

- `price` (Decimal, required)
  - Current or latest price
  - Constraints: must be > 0, precision to 4 decimal places
  - Example: Decimal("150.2500")

- `timestamp` (datetime, required)
  - When the price was recorded
  - Constraints: timezone-aware UTC, cannot be >5 minutes in future
  - Example: datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc)

- `volume` (int, required)
  - Trading volume
  - Constraints: >= 0
  - Example: 1000000

- `source` (str, required)
  - Origin of the data
  - Constraints: non-empty string
  - Example: "iex_cloud", "polygon_io"

**Example Instance**:
```python
MarketData(
    symbol="AAPL",
    price=Decimal("175.4300"),
    timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
    volume=2500000,
    source="iex_cloud"
)
```

## TradeData Schema

**Purpose**: Normalized representation of trade execution data.

**Fields**:
- `trade_id` (str, required)
  - Unique identifier for the trade
  - Constraints: non-empty, unique within client_id
  - Example: "TRD-2025-0001"

- `client_id` (str, required)
  - Client who executed the trade
  - Constraints: non-empty
  - Example: "CLIENT-001"

- `symbol` (str, required)
  - Stock ticker symbol
  - Constraints: uppercase only, 1-10 characters, alphanumeric
  - Example: "AAPL"

- `side` (Literal["BUY", "SELL"], required)
  - Trade direction
  - Constraints: must be exactly "BUY" or "SELL"
  - Example: "BUY"

- `quantity` (Decimal, required)
  - Number of shares
  - Constraints: > 0, precision to 4 decimal places
  - Example: Decimal("100.0000")

- `price` (Decimal, required)
  - Execution price per share
  - Constraints: > 0, precision to 4 decimal places
  - Example: Decimal("175.4300")

- `timestamp` (datetime, required)
  - When the trade was executed
  - Constraints: timezone-aware UTC, cannot be >5 minutes in future
  - Example: datetime(2025, 1, 15, 14, 30, 15, tzinfo=timezone.utc)

- `venue` (str, required)
  - Exchange or venue where trade executed
  - Constraints: non-empty
  - Example: "NYSE", "NASDAQ", "IEX"

**Example Instance**:
```python
TradeData(
    trade_id="TRD-2025-0001",
    client_id="CLIENT-001",
    symbol="AAPL",
    side="BUY",
    quantity=Decimal("100.0000"),
    price=Decimal("175.4300"),
    timestamp=datetime(2025, 1, 15, 14, 30, 15, tzinfo=timezone.utc),
    venue="NASDAQ"
)
```
