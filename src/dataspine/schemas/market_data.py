"""
Market Data Schema for Dataspine.

This module defines the canonical MarketData schema used for normalized
market price and volume data from any source. All market data ingested
into the system must conform to this schema after normalization.

Example Usage:
    >>> from decimal import Decimal
    >>> from datetime import datetime, timezone
    >>> from dataspine.schemas.market_data import MarketData
    >>>
    >>> # Create a valid MarketData instance
    >>> market_data = MarketData(
    ...     symbol="AAPL",
    ...     price=Decimal("175.4300"),
    ...     timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
    ...     volume=2500000,
    ...     source="iex_cloud"
    ... )
    >>>
    >>> # Access fields
    >>> print(market_data.symbol)  # "AAPL"
    >>> print(market_data.price)   # Decimal("175.4300")
    >>>
    >>> # Serialize to dict
    >>> data_dict = market_data.model_dump()

Contracts Enforced:
    - REQUIRED_FIELDS: All fields must be non-null
    - SYMBOL_FORMAT: Uppercase, 1-10 chars, alphanumeric + period only
    - PRICE_VALIDITY: Must be > 0, max 4 decimal places
    - TIMESTAMP_VALIDITY: Timezone-aware UTC, not >5min future, not before 2000
"""

import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Constants for validation
SYMBOL_PATTERN = re.compile(r'^[A-Z0-9.]{1,10}$')
MAX_DECIMAL_PLACES = 4
MAX_FUTURE_MINUTES = 5
MIN_VALID_YEAR = 2000


class MarketData(BaseModel):
    """
    Normalized representation of market price and volume data from any source.

    This schema enforces strict validation rules (data contracts) to ensure
    data quality and consistency across all market data sources.

    Attributes:
        symbol: Stock ticker symbol (e.g., "AAPL", "MSFT", "BRK.B").
                Must be uppercase, 1-10 characters, alphanumeric with periods allowed.
        price: Current or latest price as a Decimal.
               Must be positive with at most 4 decimal places.
        timestamp: When the price was recorded.
                   Must be timezone-aware UTC, not more than 5 minutes in the future.
        volume: Trading volume as an integer. Must be >= 0.
        source: Origin of the data (e.g., "iex_cloud", "polygon_io").
                Must be a non-empty string.

    Example:
        >>> from decimal import Decimal
        >>> from datetime import datetime, timezone
        >>> MarketData(
        ...     symbol="AAPL",
        ...     price=Decimal("175.4300"),
        ...     timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
        ...     volume=2500000,
        ...     source="iex_cloud"
        ... )
    """

    model_config = ConfigDict(
        validate_assignment=True,
        strict=True,
        frozen=False,
    )

    symbol: str = Field(
        ...,
        description="Stock ticker symbol (uppercase, 1-10 chars, alphanumeric + period)",
        examples=["AAPL", "MSFT", "BRK.B"],
    )
    price: Decimal = Field(
        ...,
        description="Current or latest price (must be > 0, max 4 decimal places)",
        examples=[Decimal("175.4300"), Decimal("150.25")],
    )
    timestamp: datetime = Field(
        ...,
        description="When the price was recorded (timezone-aware UTC)",
        examples=[datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc)],
    )
    volume: int = Field(
        ...,
        description="Trading volume (must be >= 0)",
        examples=[2500000, 1000000],
    )
    source: str = Field(
        ...,
        description="Origin of the data",
        examples=["iex_cloud", "polygon_io"],
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """
        Validate symbol format according to SYMBOL_FORMAT contract.

        Rules:
            - Must be uppercase only (A-Z, 0-9, period allowed)
            - Must be 1-10 characters long
            - No whitespace allowed

        Raises:
            ValueError: If symbol doesn't meet format requirements.
        """
        if not v:
            raise ValueError("SYMBOL_FORMAT: symbol cannot be empty")

        if v != v.upper():
            raise ValueError(
                f"SYMBOL_FORMAT: symbol must be uppercase only, got '{v}'"
            )

        if len(v) < 1 or len(v) > 10:
            raise ValueError(
                f"SYMBOL_FORMAT: symbol must be 1-10 characters, got {len(v)} characters"
            )

        if not SYMBOL_PATTERN.match(v):
            raise ValueError(
                f"SYMBOL_FORMAT: symbol must contain only uppercase letters, digits, "
                f"and periods (no whitespace), got '{v}'"
            )

        return v

    @field_validator("price", mode="before")
    @classmethod
    def validate_price(cls, v: Any) -> Decimal:
        """
        Validate price according to PRICE_VALIDITY contract.

        Rules:
            - Must be > 0
            - Must be numeric (Decimal type)
            - Must have <= 4 decimal places

        Raises:
            ValueError: If price doesn't meet validity requirements.
        """
        # Convert to Decimal if needed
        if not isinstance(v, Decimal):
            try:
                v = Decimal(str(v))
            except (InvalidOperation, TypeError, ValueError) as e:
                raise ValueError(
                    f"PRICE_VALIDITY: price must be a valid decimal number, got '{v}'"
                ) from e

        if v <= 0:
            raise ValueError(
                f"PRICE_VALIDITY: price must be positive, got {v}"
            )

        # Check decimal places
        sign, digits, exponent = v.as_tuple()
        if exponent < 0 and abs(exponent) > MAX_DECIMAL_PLACES:
            raise ValueError(
                f"PRICE_VALIDITY: price must have at most {MAX_DECIMAL_PLACES} decimal places, "
                f"got {abs(exponent)} decimal places in {v}"
            )

        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        """
        Validate timestamp according to TIMESTAMP_VALIDITY contract.

        Rules:
            - Must be timezone-aware
            - Must use UTC timezone
            - Must NOT be more than 5 minutes in the future
            - Must NOT be before year 2000

        Raises:
            ValueError: If timestamp doesn't meet validity requirements.
        """
        if v.tzinfo is None:
            raise ValueError(
                "TIMESTAMP_VALIDITY: timestamp must be timezone-aware"
            )

        # Check if UTC (tzinfo.utcoffset() should be 0)
        utc_offset = v.utcoffset()
        if utc_offset is None or utc_offset != timedelta(0):
            raise ValueError(
                f"TIMESTAMP_VALIDITY: timestamp must be in UTC, got offset {utc_offset}"
            )

        # Check not too far in the future
        now_utc = datetime.now(timezone.utc)
        max_future = now_utc + timedelta(minutes=MAX_FUTURE_MINUTES)
        if v > max_future:
            raise ValueError(
                f"TIMESTAMP_VALIDITY: timestamp cannot be >5min in future, got {v.isoformat()}"
            )

        # Sanity check: not before year 2000
        if v.year < MIN_VALID_YEAR:
            raise ValueError(
                f"TIMESTAMP_VALIDITY: timestamp cannot be before year {MIN_VALID_YEAR}, "
                f"got year {v.year}"
            )

        return v

    @field_validator("volume")
    @classmethod
    def validate_volume(cls, v: int) -> int:
        """
        Validate volume is non-negative.

        Rules:
            - Must be >= 0

        Raises:
            ValueError: If volume is negative.
        """
        if v < 0:
            raise ValueError(
                f"VOLUME_VALIDITY: volume must be >= 0, got {v}"
            )

        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        """
        Validate source is non-empty.

        Rules:
            - Must be non-empty string

        Raises:
            ValueError: If source is empty.
        """
        if not v or not v.strip():
            raise ValueError(
                "REQUIRED_FIELDS: source cannot be empty"
            )

        return v
