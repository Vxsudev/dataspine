# SOURCE REGISTRY

## Market Data Sources

### 1. IEX Cloud
- **Endpoint**: `/stock/{symbol}/quote`
- **Method**: GET
- **Fields**:
  - `symbol` (string): Stock ticker symbol
  - `latestPrice` (float): Most recent trade price
  - `latestUpdate` (timestamp): Last update time in milliseconds
  - `volume` (integer): Trading volume
  - `high` (float): Day's high price
  - `low` (float): Day's low price
  - `open` (float): Opening price
  - `close` (float): Previous close price
- **Frequency**: 15-minute delayed
- **Format**: JSON
- **Authentication**: API key required

### 2. Polygon.io
- **Endpoint**: `/v2/aggs/ticker/{ticker}/range/1/day/{from}/{to}`
- **Method**: GET
- **Fields**:
  - `ticker` (string): Stock symbol
  - `timestamp` (integer): Unix timestamp in milliseconds
  - `open` (float): Opening price
  - `high` (float): High price
  - `low` (float): Low price
  - `close` (float): Closing price
  - `volume` (integer): Trading volume
- **Frequency**: Daily aggregates
- **Format**: JSON
- **Authentication**: API key required

## Trade Data Sources

### 1. Execution Feed CSV
- **Source**: Internal execution system
- **Fields**:
  - `trade_id` (string): Unique trade identifier
  - `client_id` (string): Client identifier
  - `symbol` (string): Stock ticker
  - `side` (string): "BUY" or "SELL"
  - `quantity` (decimal): Number of shares
  - `price` (decimal): Execution price
  - `timestamp` (ISO 8601): Execution timestamp
  - `venue` (string): Execution venue name
  - `commission` (decimal, optional): Commission charged
  - `fees` (decimal, optional): Regulatory fees
- **Frequency**: Real-time stream
- **Format**: CSV with headers
- **Delivery**: SFTP drop every 5 minutes
