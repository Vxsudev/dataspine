"""
Trade Data Schema for Dataspine.

This module defines the canonical TradeData schema used for normalized
trade execution data. All trade data ingested into the system must
conform to this schema after normalization.

Example Usage:
    >>> from decimal import Decimal
    >>> from datetime import datetime, timezone
    >>> from dataspine.schemas.trade_data import TradeData
    >>>
    >>> # Create a valid TradeData instance
    >>> trade_data = TradeData(
    ...     trade_id="TRD-2025-0001",
    ...     client_id="CLIENT-001",
    ...     symbol="AAPL",
    ...     side="BUY",
    ...     quantity=Decimal("100.0000"),
    ...     price=Decimal("175.4300"),
    ...     timestamp=datetime(2025, 1, 15, 14, 30, 15, tzinfo=timezone.utc),
    ...     venue="NASDAQ"
    ... )
    >>>
    >>> # Access fields
    >>> print(trade_data.trade_id)  # "TRD-2025-0001"
    >>> print(trade_data.side)      # "BUY"
    >>>
    >>> # Serialize to dict
    >>> data_dict = trade_data.model_dump()

Contracts Enforced:
    - REQUIRED_FIELDS: All fields must be non-null
    - SYMBOL_FORMAT: Uppercase, 1-10 chars, alphanumeric + period only
    - PRICE_VALIDITY: Must be > 0, max 4 decimal places
    - TIMESTAMP_VALIDITY: Timezone-aware UTC, not >5min future, not before 2000
    - TRADE_SPECIFIC: side must be "BUY" or "SELL", quantity > 0
"""

import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Constants for validation
SYMBOL_PATTERN = re.compile(r'^[A-Z0-9.]{1,10}$')
MAX_DECIMAL_PLACES = 4
MAX_FUTURE_MINUTES = 5
MIN_VALID_YEAR = 2000
VALID_SIDES = ("BUY", "SELL")


class TradeData(BaseModel):
    """
    Normalized representation of trade execution data.

    This schema enforces strict validation rules (data contracts) to ensure
    data quality and consistency across all trade data sources.

    Attributes:
        trade_id: Unique identifier for the trade (e.g., "TRD-2025-0001").
                  Must be non-empty, unique within client_id scope.
        client_id: Client who executed the trade (e.g., "CLIENT-001").
                   Must be non-empty.
        symbol: Stock ticker symbol (e.g., "AAPL").
                Must be uppercase, 1-10 characters, alphanumeric with periods allowed.
        side: Trade direction. Must be exactly "BUY" or "SELL".
        quantity: Number of shares as a Decimal.
                  Must be > 0 with at most 4 decimal places.
        price: Execution price per share as a Decimal.
               Must be > 0 with at most 4 decimal places.
        timestamp: When the trade was executed.
                   Must be timezone-aware UTC, not more than 5 minutes in the future.
        venue: Exchange or venue where trade executed (e.g., "NYSE", "NASDAQ").
               Must be non-empty.

    Example:
        >>> from decimal import Decimal
        >>> from datetime import datetime, timezone
        >>> TradeData(
        ...     trade_id="TRD-2025-0001",
        ...     client_id="CLIENT-001",
        ...     symbol="AAPL",
        ...     side="BUY",
        ...     quantity=Decimal("100.0000"),
        ...     price=Decimal("175.4300"),
        ...     timestamp=datetime(2025, 1, 15, 14, 30, 15, tzinfo=timezone.utc),
        ...     venue="NASDAQ"
        ... )
    """

    model_config = ConfigDict(
        validate_assignment=True,
        strict=True,
        frozen=False,
    )

    trade_id: str = Field(
        ...,
        description="Unique identifier for the trade",
        examples=["TRD-2025-0001", "TRD-2025-0002"],
    )
    client_id: str = Field(
        ...,
        description="Client who executed the trade",
        examples=["CLIENT-001", "CLIENT-002"],
    )
    symbol: str = Field(
        ...,
        description="Stock ticker symbol (uppercase, 1-10 chars, alphanumeric + period)",
        examples=["AAPL", "MSFT", "BRK.B"],
    )
    side: Literal["BUY", "SELL"] = Field(
        ...,
        description="Trade direction (must be exactly 'BUY' or 'SELL')",
        examples=["BUY", "SELL"],
    )
    quantity: Decimal = Field(
        ...,
        description="Number of shares (must be > 0, max 4 decimal places)",
        examples=[Decimal("100.0000"), Decimal("50.5")],
    )
    price: Decimal = Field(
        ...,
        description="Execution price per share (must be > 0, max 4 decimal places)",
        examples=[Decimal("175.4300"), Decimal("150.25")],
    )
    timestamp: datetime = Field(
        ...,
        description="When the trade was executed (timezone-aware UTC)",
        examples=[datetime(2025, 1, 15, 14, 30, 15, tzinfo=timezone.utc)],
    )
    venue: str = Field(
        ...,
        description="Exchange or venue where trade executed",
        examples=["NYSE", "NASDAQ", "IEX"],
    )

    @field_validator("trade_id")
    @classmethod
    def validate_trade_id(cls, v: str) -> str:
        """
        Validate trade_id is non-empty.

        Rules:
            - Must be non-empty string

        Raises:
            ValueError: If trade_id is empty.
        """
        if not v or not v.strip():
            raise ValueError(
                "REQUIRED_FIELDS: trade_id cannot be empty"
            )

        return v

    @field_validator("client_id")
    @classmethod
    def validate_client_id(cls, v: str) -> str:
        """
        Validate client_id is non-empty.

        Rules:
            - Must be non-empty string

        Raises:
            ValueError: If client_id is empty.
        """
        if not v or not v.strip():
            raise ValueError(
                "REQUIRED_FIELDS: client_id cannot be empty"
            )

        return v

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

    @field_validator("side", mode="before")
    @classmethod
    def validate_side(cls, v: Any) -> str:
        """
        Validate side according to TRADE_SPECIFIC contract.

        Rules:
            - Must be exactly "BUY" or "SELL" (no case variations)

        Raises:
            ValueError: If side is not exactly "BUY" or "SELL".
        """
        if v not in VALID_SIDES:
            raise ValueError(
                f"TRADE_SPECIFIC: side must be exactly 'BUY' or 'SELL', got '{v}'"
            )

        return v

    @field_validator("quantity", mode="before")
    @classmethod
    def validate_quantity(cls, v: Any) -> Decimal:
        """
        Validate quantity according to PRICE_VALIDITY contract.

        Rules:
            - Must be > 0
            - Must be numeric (Decimal type)
            - Must have <= 4 decimal places

        Raises:
            ValueError: If quantity doesn't meet validity requirements.
        """
        # Convert to Decimal if needed
        if not isinstance(v, Decimal):
            try:
                v = Decimal(str(v))
            except (InvalidOperation, TypeError, ValueError) as e:
                raise ValueError(
                    f"QUANTITY_VALIDITY: quantity must be a valid decimal number, got '{v}'"
                ) from e

        if v <= 0:
            raise ValueError(
                f"QUANTITY_VALIDITY: quantity must be positive, got {v}"
            )

        # Check decimal places
        sign, digits, exponent = v.as_tuple()
        if exponent < 0 and abs(exponent) > MAX_DECIMAL_PLACES:
            raise ValueError(
                f"QUANTITY_VALIDITY: quantity must have at most {MAX_DECIMAL_PLACES} decimal places, "
                f"got {abs(exponent)} decimal places in {v}"
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

    @field_validator("venue")
    @classmethod
    def validate_venue(cls, v: str) -> str:
        """
        Validate venue is non-empty.

        Rules:
            - Must be non-empty string

        Raises:
            ValueError: If venue is empty.
        """
        if not v or not v.strip():
            raise ValueError(
                "REQUIRED_FIELDS: venue cannot be empty"
            )

        return v
