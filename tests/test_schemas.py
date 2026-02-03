"""
Pytest test suite for dataspine schemas.

Tests MarketData and TradeData Pydantic models for:
- Valid data acceptance
- Field validation rules
- Error message clarity
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from dataspine.schemas import MarketData, TradeData


class TestMarketDataValid:
    """Tests for valid MarketData instances."""

    @pytest.mark.smoke
    def test_market_data_valid(self):
        """Create valid MarketData instance and verify all fields set correctly."""
        md = MarketData(
            symbol="AAPL",
            price=Decimal("175.4300"),
            timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC),
            volume=2500000,
            source="iex_cloud",
        )

        assert md.symbol == "AAPL", "Symbol should be AAPL"
        assert md.price == Decimal("175.4300"), "Price should be 175.4300"
        assert md.volume == 2500000, "Volume should be 2500000"
        assert md.source == "iex_cloud", "Source should be iex_cloud"
        assert md.timestamp.tzinfo is not None, "Timestamp should be timezone-aware"

    def test_market_data_valid_with_period_symbol(self):
        """Test that class share symbols with periods are accepted."""
        md = MarketData(
            symbol="BRK.B",
            price=Decimal("450.00"),
            timestamp=datetime.now(UTC),
            volume=100000,
            source="polygon_io",
        )

        assert md.symbol == "BRK.B", "Symbol with period should be accepted"

    def test_market_data_valid_minimum_values(self):
        """Test MarketData with minimum valid values."""
        md = MarketData(
            symbol="A",
            price=Decimal("0.0001"),
            timestamp=datetime(2000, 1, 1, 0, 0, 0, tzinfo=UTC),
            volume=0,
            source="x",
        )

        assert md.symbol == "A", "Single character symbol should be valid"
        assert md.price == Decimal("0.0001"), "Small positive price should be valid"
        assert md.volume == 0, "Zero volume should be valid"


class TestMarketDataInvalidSymbol:
    """Tests for MarketData symbol validation."""

    @pytest.mark.smoke
    def test_market_data_invalid_symbol_lowercase(self):
        """Lowercase symbol should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketData(
                symbol="aapl",
                price=Decimal("175.43"),
                timestamp=datetime.now(UTC),
                volume=1000000,
                source="test",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"
        error_msg = str(errors[0]["msg"]).lower()
        assert "uppercase" in error_msg or "symbol" in error_msg, (
            f"Error should mention symbol case issue, got: {errors[0]['msg']}"
        )

    def test_market_data_invalid_symbol_too_long(self):
        """Symbol longer than 10 characters should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketData(
                symbol="ABCDEFGHIJKLMNO",  # 15 characters
                price=Decimal("100.00"),
                timestamp=datetime.now(UTC),
                volume=1000,
                source="test",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"
        error_msg = str(errors[0]["msg"]).lower()
        assert "character" in error_msg or "1-10" in error_msg, (
            f"Error should mention character limit, got: {errors[0]['msg']}"
        )

    def test_market_data_invalid_symbol_empty(self):
        """Empty symbol should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketData(
                symbol="",
                price=Decimal("100.00"),
                timestamp=datetime.now(UTC),
                volume=1000,
                source="test",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"

    def test_market_data_invalid_symbol_whitespace(self):
        """Symbol with whitespace should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketData(
                symbol="AA PL",
                price=Decimal("100.00"),
                timestamp=datetime.now(UTC),
                volume=1000,
                source="test",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"


class TestMarketDataInvalidPrice:
    """Tests for MarketData price validation."""

    @pytest.mark.smoke
    def test_market_data_invalid_price_negative(self):
        """Negative price should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketData(
                symbol="AAPL",
                price=Decimal("-10.50"),
                timestamp=datetime.now(UTC),
                volume=1000000,
                source="test",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"
        error_msg = str(errors[0]["msg"]).lower()
        assert "positive" in error_msg or "price" in error_msg, (
            f"Error should mention price must be positive, got: {errors[0]['msg']}"
        )

    def test_market_data_invalid_price_zero(self):
        """Zero price should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketData(
                symbol="AAPL",
                price=Decimal("0"),
                timestamp=datetime.now(UTC),
                volume=1000000,
                source="test",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"
        error_msg = str(errors[0]["msg"]).lower()
        assert "positive" in error_msg or "price" in error_msg, (
            f"Error should mention price must be positive, got: {errors[0]['msg']}"
        )

    def test_market_data_invalid_price_too_many_decimals(self):
        """Price with more than 4 decimal places should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketData(
                symbol="AAPL",
                price=Decimal("100.123456"),
                timestamp=datetime.now(UTC),
                volume=1000000,
                source="test",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"
        error_msg = str(errors[0]["msg"]).lower()
        assert "decimal" in error_msg, (
            f"Error should mention decimal places, got: {errors[0]['msg']}"
        )


class TestMarketDataInvalidTimestamp:
    """Tests for MarketData timestamp validation."""

    def test_market_data_invalid_timestamp_naive(self):
        """Naive datetime (no timezone) should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketData(
                symbol="AAPL",
                price=Decimal("175.43"),
                timestamp=datetime(2025, 1, 15, 14, 30, 0),  # No tzinfo
                volume=1000000,
                source="test",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"
        error_msg = str(errors[0]["msg"]).lower()
        assert "timezone" in error_msg or "aware" in error_msg, (
            f"Error should mention timezone, got: {errors[0]['msg']}"
        )

    def test_market_data_invalid_timestamp_future(self):
        """Timestamp more than 5 minutes in future should be rejected."""
        future_time = datetime.now(UTC) + timedelta(hours=1)

        with pytest.raises(ValidationError) as exc_info:
            MarketData(
                symbol="AAPL",
                price=Decimal("175.43"),
                timestamp=future_time,
                volume=1000000,
                source="test",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"
        error_msg = str(errors[0]["msg"]).lower()
        assert "future" in error_msg or "5min" in error_msg or "5 min" in error_msg, (
            f"Error should mention future timestamp, got: {errors[0]['msg']}"
        )

    def test_market_data_invalid_timestamp_too_old(self):
        """Timestamp before year 2000 should be rejected."""
        old_time = datetime(1999, 12, 31, 23, 59, 59, tzinfo=UTC)

        with pytest.raises(ValidationError) as exc_info:
            MarketData(
                symbol="AAPL",
                price=Decimal("175.43"),
                timestamp=old_time,
                volume=1000000,
                source="test",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"
        error_msg = str(errors[0]["msg"]).lower()
        assert "2000" in error_msg or "year" in error_msg, (
            f"Error should mention year 2000, got: {errors[0]['msg']}"
        )


class TestMarketDataInvalidVolume:
    """Tests for MarketData volume validation."""

    def test_market_data_invalid_volume_negative(self):
        """Negative volume should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketData(
                symbol="AAPL",
                price=Decimal("175.43"),
                timestamp=datetime.now(UTC),
                volume=-100,
                source="test",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"
        error_msg = str(errors[0]["msg"]).lower()
        assert "volume" in error_msg or ">= 0" in error_msg or "negative" in error_msg, (
            f"Error should mention volume constraint, got: {errors[0]['msg']}"
        )


class TestTradeDataValid:
    """Tests for valid TradeData instances."""

    @pytest.mark.smoke
    def test_trade_data_valid(self):
        """Create valid TradeData instance and verify all fields set correctly."""
        td = TradeData(
            trade_id="TRD-2025-0001",
            client_id="CLIENT-001",
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("100.0000"),
            price=Decimal("175.4300"),
            timestamp=datetime(2025, 1, 15, 14, 30, 15, tzinfo=UTC),
            venue="NASDAQ",
        )

        assert td.trade_id == "TRD-2025-0001", "trade_id should match"
        assert td.client_id == "CLIENT-001", "client_id should match"
        assert td.symbol == "AAPL", "Symbol should be AAPL"
        assert td.side == "BUY", "Side should be BUY"
        assert td.quantity == Decimal("100.0000"), "Quantity should match"
        assert td.price == Decimal("175.4300"), "Price should match"
        assert td.venue == "NASDAQ", "Venue should be NASDAQ"

    def test_trade_data_valid_sell(self):
        """Test TradeData with SELL side."""
        td = TradeData(
            trade_id="TRD-2025-0002",
            client_id="CLIENT-001",
            symbol="MSFT",
            side="SELL",
            quantity=Decimal("50.0000"),
            price=Decimal("400.0000"),
            timestamp=datetime.now(UTC),
            venue="NYSE",
        )

        assert td.side == "SELL", "Side should be SELL"


class TestTradeDataInvalidSide:
    """Tests for TradeData side validation."""

    @pytest.mark.smoke
    def test_trade_data_invalid_side_lowercase(self):
        """Lowercase side should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeData(
                trade_id="TRD-001",
                client_id="CLIENT-001",
                symbol="AAPL",
                side="buy",  # lowercase
                quantity=Decimal("100"),
                price=Decimal("175.43"),
                timestamp=datetime.now(UTC),
                venue="NYSE",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"
        error_msg = str(errors[0]["msg"]).lower()
        assert "buy" in error_msg or "sell" in error_msg or "side" in error_msg, (
            f"Error should mention valid side values, got: {errors[0]['msg']}"
        )

    def test_trade_data_invalid_side_hold(self):
        """Invalid side value 'HOLD' should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeData(
                trade_id="TRD-001",
                client_id="CLIENT-001",
                symbol="AAPL",
                side="HOLD",
                quantity=Decimal("100"),
                price=Decimal("175.43"),
                timestamp=datetime.now(UTC),
                venue="NYSE",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"


class TestTradeDataInvalidQuantity:
    """Tests for TradeData quantity validation."""

    def test_trade_data_invalid_quantity_zero(self):
        """Zero quantity should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeData(
                trade_id="TRD-001",
                client_id="CLIENT-001",
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("0"),
                price=Decimal("175.43"),
                timestamp=datetime.now(UTC),
                venue="NYSE",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"
        error_msg = str(errors[0]["msg"]).lower()
        assert "quantity" in error_msg or "positive" in error_msg, (
            f"Error should mention quantity must be positive, got: {errors[0]['msg']}"
        )

    def test_trade_data_invalid_quantity_negative(self):
        """Negative quantity should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeData(
                trade_id="TRD-001",
                client_id="CLIENT-001",
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("-100"),
                price=Decimal("175.43"),
                timestamp=datetime.now(UTC),
                venue="NYSE",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"


class TestTradeDataInvalidRequired:
    """Tests for TradeData required field validation."""

    def test_trade_data_invalid_trade_id_empty(self):
        """Empty trade_id should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeData(
                trade_id="",
                client_id="CLIENT-001",
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("100"),
                price=Decimal("175.43"),
                timestamp=datetime.now(UTC),
                venue="NYSE",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"

    def test_trade_data_invalid_venue_empty(self):
        """Empty venue should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TradeData(
                trade_id="TRD-001",
                client_id="CLIENT-001",
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("100"),
                price=Decimal("175.43"),
                timestamp=datetime.now(UTC),
                venue="",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1, "Should have at least one error"
