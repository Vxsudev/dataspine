"""
Contract validation for dataspine.

This module implements data contract validation as defined in docs/contracts.md.
All data must pass these validations after normalization before being accepted
into the system.

Contracts Implemented:
    - Contract 1: Required Fields
    - Contract 2: Price Validity
    - Contract 3: Timestamp Validity
    - Contract 4: Symbol Format
    - Contract 5: Trade-Specific Rules

Example Usage:
    >>> from dataspine.validation.contracts import ContractValidator
    >>> from dataspine.schemas import MarketData, TradeData
    >>> from decimal import Decimal
    >>> from datetime import UTC, datetime
    >>>
    >>> validator = ContractValidator()
    >>>
    >>> # Validate market data
    >>> market_data = MarketData(
    ...     symbol="AAPL",
    ...     price=Decimal("175.43"),
    ...     timestamp=datetime.now(UTC),
    ...     volume=1000000,
    ...     source="iex_cloud"
    ... )
    >>> is_valid, errors = validator.validate_market_data(market_data)
    >>> print(f"Valid: {is_valid}, Errors: {errors}")
"""

import logging
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from dataspine.schemas.market_data import MarketData
from dataspine.schemas.trade_data import TradeData

logger = logging.getLogger(__name__)

# Constants for validation
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.]{1,10}$")
MAX_DECIMAL_PLACES = 4
MAX_FUTURE_MINUTES = 5
MIN_VALID_YEAR = 2000
VALID_SIDES = ("BUY", "SELL")


class ContractValidator:
    """
    Validates data against defined contracts.

    This class provides methods to validate MarketData and TradeData instances
    against the data contracts defined in the system. Each contract check is
    performed independently, and all violations are collected and returned.

    Attributes:
        None

    Example:
        >>> validator = ContractValidator()
        >>> is_valid, errors = validator.validate_market_data(data)
        >>> if not is_valid:
        ...     for error in errors:
        ...         print(f"Contract violation: {error}")
    """

    def validate_market_data(self, data: MarketData) -> tuple[bool, list[str]]:
        """
        Validate MarketData against all applicable contracts.

        Validates the following contracts:
            - Contract 1: Required Fields (enforced by Pydantic, verified here)
            - Contract 2: Price Validity
            - Contract 3: Timestamp Validity
            - Contract 4: Symbol Format

        Args:
            data: MarketData instance to validate.

        Returns:
            Tuple of (is_valid, errors):
                - is_valid: True if all contracts pass, False otherwise
                - errors: List of error messages for failed contracts

        Example:
            >>> validator = ContractValidator()
            >>> is_valid, errors = validator.validate_market_data(market_data)
            >>> if not is_valid:
            ...     print(f"Validation failed: {errors}")
        """
        errors: list[str] = []

        # Contract 1: Required Fields
        errors.extend(self._check_required_fields_market(data))

        # Contract 2: Price Validity
        errors.extend(self._check_price_validity(data.price, "price"))

        # Contract 3: Timestamp Validity
        errors.extend(self._check_timestamp_validity(data.timestamp))

        # Contract 4: Symbol Format
        errors.extend(self._check_symbol_format(data.symbol))

        is_valid = len(errors) == 0

        if not is_valid:
            logger.warning(
                "Market data validation failed",
                extra={
                    "extra_fields": {
                        "symbol": data.symbol,
                        "source": data.source,
                        "error_count": len(errors),
                        "errors": errors,
                    }
                },
            )

        return is_valid, errors

    def validate_trade_data(self, data: TradeData) -> tuple[bool, list[str]]:
        """
        Validate TradeData against all applicable contracts.

        Validates the following contracts:
            - Contract 1: Required Fields (enforced by Pydantic, verified here)
            - Contract 2: Price Validity (price and quantity)
            - Contract 3: Timestamp Validity
            - Contract 4: Symbol Format
            - Contract 5: Trade-Specific Rules

        Args:
            data: TradeData instance to validate.

        Returns:
            Tuple of (is_valid, errors):
                - is_valid: True if all contracts pass, False otherwise
                - errors: List of error messages for failed contracts

        Example:
            >>> validator = ContractValidator()
            >>> is_valid, errors = validator.validate_trade_data(trade_data)
            >>> if not is_valid:
            ...     print(f"Validation failed: {errors}")
        """
        errors: list[str] = []

        # Contract 1: Required Fields
        errors.extend(self._check_required_fields_trade(data))

        # Contract 2: Price Validity (for both price and quantity)
        errors.extend(self._check_price_validity(data.price, "price"))
        errors.extend(self._check_price_validity(data.quantity, "quantity"))

        # Contract 3: Timestamp Validity
        errors.extend(self._check_timestamp_validity(data.timestamp))

        # Contract 4: Symbol Format
        errors.extend(self._check_symbol_format(data.symbol))

        # Contract 5: Trade-Specific Rules
        errors.extend(self._check_trade_specific_rules(data))

        is_valid = len(errors) == 0

        if not is_valid:
            logger.warning(
                "Trade data validation failed",
                extra={
                    "extra_fields": {
                        "trade_id": data.trade_id,
                        "client_id": data.client_id,
                        "symbol": data.symbol,
                        "error_count": len(errors),
                        "errors": errors,
                    }
                },
            )

        return is_valid, errors

    def _check_required_fields_market(self, data: MarketData) -> list[str]:
        """
        Check Contract 1: Required Fields for MarketData.

        Note: Pydantic already enforces required fields, but we verify here
        for explicit contract documentation and additional null checks.

        Args:
            data: MarketData instance to check.

        Returns:
            List of error messages for missing fields.
        """
        errors: list[str] = []
        required_fields = ["symbol", "price", "timestamp", "volume", "source"]

        for field in required_fields:
            value = getattr(data, field, None)
            if value is None:
                errors.append(f"REQUIRED_FIELDS: Missing required field {field}")

        return errors

    def _check_required_fields_trade(self, data: TradeData) -> list[str]:
        """
        Check Contract 1: Required Fields for TradeData.

        Note: Pydantic already enforces required fields, but we verify here
        for explicit contract documentation and additional null checks.

        Args:
            data: TradeData instance to check.

        Returns:
            List of error messages for missing fields.
        """
        errors: list[str] = []
        required_fields = [
            "trade_id",
            "client_id",
            "symbol",
            "side",
            "quantity",
            "price",
            "timestamp",
            "venue",
        ]

        for field in required_fields:
            value = getattr(data, field, None)
            if value is None:
                errors.append(f"REQUIRED_FIELDS: Missing required field {field}")

        return errors

    def _check_price_validity(self, value: Decimal, field_name: str) -> list[str]:
        """
        Check Contract 2: Price Validity.

        Rules:
            - Must be > 0
            - Must be Decimal type
            - Must have <= 4 decimal places

        Args:
            value: The price or quantity value to check.
            field_name: Name of the field being checked (for error messages).

        Returns:
            List of error messages for price validity violations.
        """
        errors: list[str] = []

        # Check type
        if not isinstance(value, Decimal):
            errors.append(
                f"PRICE_VALIDITY: {field_name} must be Decimal type, "
                f"got {type(value).__name__}"
            )
            return errors  # Can't check further if not Decimal

        # Check positive
        if value <= 0:
            errors.append(
                f"PRICE_VALIDITY: {field_name} must be positive, got {value}"
            )

        # Check decimal places
        sign, digits, exponent = value.as_tuple()
        if isinstance(exponent, int) and exponent < 0:
            decimal_places = abs(exponent)
            if decimal_places > MAX_DECIMAL_PLACES:
                errors.append(
                    f"PRICE_VALIDITY: {field_name} must have at most "
                    f"{MAX_DECIMAL_PLACES} decimal places, got {decimal_places}"
                )

        return errors

    def _check_timestamp_validity(self, ts: datetime) -> list[str]:
        """
        Check Contract 3: Timestamp Validity.

        Rules:
            - Must be timezone-aware
            - Must use UTC timezone
            - Must NOT be more than 5 minutes in the future
            - Must NOT be before year 2000

        Args:
            ts: The timestamp to check.

        Returns:
            List of error messages for timestamp validity violations.
        """
        errors: list[str] = []

        # Check timezone-aware
        if ts.tzinfo is None:
            errors.append("TIMESTAMP_VALIDITY: timestamp must be timezone-aware")
            return errors  # Can't check UTC if not timezone-aware

        # Check UTC
        utc_offset = ts.utcoffset()
        if utc_offset is None or utc_offset != timedelta(0):
            errors.append(
                f"TIMESTAMP_VALIDITY: timestamp must be in UTC, got offset {utc_offset}"
            )

        # Check not too far in future
        now_utc = datetime.now(UTC)
        max_future = now_utc + timedelta(minutes=MAX_FUTURE_MINUTES)
        if ts > max_future:
            errors.append(
                f"TIMESTAMP_VALIDITY: timestamp cannot be >5min in future, "
                f"got {ts.isoformat()}"
            )

        # Check not before year 2000
        if ts.year < MIN_VALID_YEAR:
            errors.append(
                f"TIMESTAMP_VALIDITY: timestamp cannot be before year "
                f"{MIN_VALID_YEAR}, got year {ts.year}"
            )

        return errors

    def _check_symbol_format(self, symbol: str) -> list[str]:
        """
        Check Contract 4: Symbol Format.

        Rules:
            - Must be uppercase only (A-Z, 0-9, period allowed)
            - Must be 1-10 characters long
            - Must be alphanumeric (plus period for class shares)
            - No whitespace allowed

        Args:
            symbol: The symbol string to check.

        Returns:
            List of error messages for symbol format violations.
        """
        errors: list[str] = []

        # Check not empty
        if not symbol:
            errors.append("SYMBOL_FORMAT: symbol cannot be empty")
            return errors

        # Check length
        if len(symbol) < 1 or len(symbol) > 10:
            errors.append(
                f"SYMBOL_FORMAT: symbol must be 1-10 characters, "
                f"got {len(symbol)} characters"
            )

        # Check uppercase
        if symbol != symbol.upper():
            errors.append(
                f"SYMBOL_FORMAT: symbol must be uppercase only, got '{symbol}'"
            )

        # Check pattern (alphanumeric + period, no whitespace)
        if not SYMBOL_PATTERN.match(symbol):
            errors.append(
                f"SYMBOL_FORMAT: symbol must contain only uppercase letters, "
                f"digits, and periods (no whitespace), got '{symbol}'"
            )

        return errors

    def _check_trade_specific_rules(self, data: TradeData) -> list[str]:
        """
        Check Contract 5: Trade-Specific Rules.

        Rules:
            - side must be exactly "BUY" or "SELL"
            - quantity must be > 0
            - trade_id must be non-empty
            - venue must be non-empty

        Args:
            data: TradeData instance to check.

        Returns:
            List of error messages for trade-specific rule violations.
        """
        errors: list[str] = []

        # Check side
        if data.side not in VALID_SIDES:
            errors.append(
                f"TRADE_SPECIFIC: side must be exactly 'BUY' or 'SELL', "
                f"got '{data.side}'"
            )

        # Check quantity > 0 (already checked in price validity, but explicit here)
        if data.quantity <= 0:
            errors.append(
                f"TRADE_SPECIFIC: quantity must be positive, got {data.quantity}"
            )

        # Check trade_id non-empty
        if not data.trade_id or not data.trade_id.strip():
            errors.append("TRADE_SPECIFIC: trade_id cannot be empty")

        # Check venue non-empty
        if not data.venue or not data.venue.strip():
            errors.append("TRADE_SPECIFIC: venue cannot be empty")

        return errors
