"""
Pytest test suite for dataspine contract validation and invariants.

Tests ContractValidator class and invariant checking functions for:
- Valid data acceptance
- Contract violation detection
- Invariant enforcement
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from dataspine.schemas import MarketData, TradeData
from dataspine.validation.contracts import ContractValidator
from dataspine.validation.invariants import (
    check_completeness,
    check_idempotency,
    check_monotonic_timestamps,
    check_referential_integrity,
    check_uniqueness,
)


class TestContractValidatorMarketData:
    """Tests for ContractValidator with MarketData."""

    @pytest.mark.smoke
    def test_contract_validator_market_valid(self):
        """Valid MarketData should pass all contracts."""
        validator = ContractValidator()

        md = MarketData(
            symbol="AAPL",
            price=Decimal("175.4300"),
            timestamp=datetime.now(UTC),
            volume=2500000,
            source="iex_cloud",
        )

        is_valid, errors = validator.validate_market_data(md)

        assert is_valid is True, f"Valid MarketData should pass, got errors: {errors}"
        assert errors == [], f"Should have no errors, got: {errors}"

    def test_contract_validator_market_invalid_price(self):
        """MarketData with invalid price should fail validation."""
        validator = ContractValidator()

        # Use model_construct to bypass Pydantic validation and test ContractValidator
        md = MarketData.model_construct(
            symbol="AAPL",
            price=Decimal("-10.50"),  # Negative price
            timestamp=datetime.now(UTC),
            volume=2500000,
            source="iex_cloud",
        )

        is_valid, errors = validator.validate_market_data(md)

        assert is_valid is False, "Negative price should fail validation"
        assert len(errors) >= 1, "Should have at least one error"
        assert any("PRICE_VALIDITY" in err for err in errors), (
            f"Should have PRICE_VALIDITY error, got: {errors}"
        )

    def test_contract_validator_market_invalid_symbol(self):
        """MarketData with invalid symbol should fail validation."""
        validator = ContractValidator()

        # Use model_construct to bypass Pydantic validation
        md = MarketData.model_construct(
            symbol="aapl",  # lowercase
            price=Decimal("175.43"),
            timestamp=datetime.now(UTC),
            volume=2500000,
            source="iex_cloud",
        )

        is_valid, errors = validator.validate_market_data(md)

        assert is_valid is False, "Lowercase symbol should fail validation"
        assert any("SYMBOL_FORMAT" in err for err in errors), (
            f"Should have SYMBOL_FORMAT error, got: {errors}"
        )

    def test_contract_validator_market_invalid_timestamp_naive(self):
        """MarketData with naive timestamp should fail validation."""
        validator = ContractValidator()

        # Use model_construct to bypass Pydantic validation
        md = MarketData.model_construct(
            symbol="AAPL",
            price=Decimal("175.43"),
            timestamp=datetime(2025, 1, 15, 14, 30, 0),  # Naive - no timezone
            volume=2500000,
            source="iex_cloud",
        )

        is_valid, errors = validator.validate_market_data(md)

        assert is_valid is False, "Naive timestamp should fail validation"
        assert any("TIMESTAMP_VALIDITY" in err for err in errors), (
            f"Should have TIMESTAMP_VALIDITY error, got: {errors}"
        )

    def test_contract_validator_market_multiple_errors(self):
        """MarketData with multiple violations should report all errors."""
        validator = ContractValidator()

        # Use model_construct to create data with multiple violations
        md = MarketData.model_construct(
            symbol="aapl",  # lowercase
            price=Decimal("-10.50"),  # negative
            timestamp=datetime(2025, 1, 15, 14, 30, 0),  # naive
            volume=-100,  # negative (not caught by ContractValidator, but good to test)
            source="iex_cloud",
        )

        is_valid, errors = validator.validate_market_data(md)

        assert is_valid is False, "Multiple violations should fail validation"
        assert len(errors) >= 2, f"Should have multiple errors, got {len(errors)}: {errors}"


class TestContractValidatorTradeData:
    """Tests for ContractValidator with TradeData."""

    @pytest.mark.smoke
    def test_contract_validator_trade_valid(self):
        """Valid TradeData should pass all contracts."""
        validator = ContractValidator()

        td = TradeData(
            trade_id="TRD-2025-0001",
            client_id="CLIENT-001",
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("100.0000"),
            price=Decimal("175.4300"),
            timestamp=datetime.now(UTC),
            venue="NASDAQ",
        )

        is_valid, errors = validator.validate_trade_data(td)

        assert is_valid is True, f"Valid TradeData should pass, got errors: {errors}"
        assert errors == [], f"Should have no errors, got: {errors}"

    def test_contract_validator_trade_invalid_side(self):
        """TradeData with invalid side should fail validation."""
        validator = ContractValidator()

        # Use model_construct to bypass Pydantic validation
        td = TradeData.model_construct(
            trade_id="TRD-001",
            client_id="CLIENT-001",
            symbol="AAPL",
            side="HOLD",  # Invalid side
            quantity=Decimal("100"),
            price=Decimal("175.43"),
            timestamp=datetime.now(UTC),
            venue="NYSE",
        )

        is_valid, errors = validator.validate_trade_data(td)

        assert is_valid is False, "Invalid side should fail validation"
        assert any("TRADE_SPECIFIC" in err for err in errors), (
            f"Should have TRADE_SPECIFIC error for side, got: {errors}"
        )

    def test_contract_validator_trade_invalid_quantity(self):
        """TradeData with zero quantity should fail validation."""
        validator = ContractValidator()

        # Use model_construct to bypass Pydantic validation
        td = TradeData.model_construct(
            trade_id="TRD-001",
            client_id="CLIENT-001",
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("0"),  # Zero quantity
            price=Decimal("175.43"),
            timestamp=datetime.now(UTC),
            venue="NYSE",
        )

        is_valid, errors = validator.validate_trade_data(td)

        assert is_valid is False, "Zero quantity should fail validation"
        # Check for either PRICE_VALIDITY (for quantity) or TRADE_SPECIFIC
        assert any("VALIDITY" in err or "TRADE_SPECIFIC" in err for err in errors), (
            f"Should have validity error for quantity, got: {errors}"
        )

    def test_contract_validator_trade_invalid_empty_venue(self):
        """TradeData with empty venue should fail validation."""
        validator = ContractValidator()

        # Use model_construct to bypass Pydantic validation
        td = TradeData.model_construct(
            trade_id="TRD-001",
            client_id="CLIENT-001",
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("100"),
            price=Decimal("175.43"),
            timestamp=datetime.now(UTC),
            venue="",  # Empty venue
        )

        is_valid, errors = validator.validate_trade_data(td)

        assert is_valid is False, "Empty venue should fail validation"
        assert any("TRADE_SPECIFIC" in err for err in errors), (
            f"Should have TRADE_SPECIFIC error for venue, got: {errors}"
        )


class TestInvariantsIdempotency:
    """Tests for idempotency invariant checking."""

    @pytest.mark.smoke
    def test_invariants_idempotency_identical(self):
        """Identical batches should pass idempotency check."""
        md1 = MarketData(
            symbol="AAPL",
            price=Decimal("175.43"),
            timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC),
            volume=1000000,
            source="test",
        )
        md2 = MarketData(
            symbol="MSFT",
            price=Decimal("400.00"),
            timestamp=datetime(2025, 1, 15, 14, 31, 0, tzinfo=UTC),
            volume=500000,
            source="test",
        )

        batch1 = [md1, md2]
        batch2 = [md1, md2]

        result = check_idempotency(batch1, batch2)

        assert result is True, "Identical batches should be idempotent"

    def test_invariants_idempotency_different_length(self):
        """Batches with different lengths should fail idempotency check."""
        md = MarketData(
            symbol="AAPL",
            price=Decimal("175.43"),
            timestamp=datetime.now(UTC),
            volume=1000000,
            source="test",
        )

        batch1 = [md, md]
        batch2 = [md]

        result = check_idempotency(batch1, batch2)

        assert result is False, "Different length batches should fail idempotency"

    def test_invariants_idempotency_different_content(self):
        """Batches with different content should fail idempotency check."""
        md1 = MarketData(
            symbol="AAPL",
            price=Decimal("175.43"),
            timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC),
            volume=1000000,
            source="test",
        )
        md2 = MarketData(
            symbol="AAPL",
            price=Decimal("176.00"),  # Different price
            timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC),
            volume=1000000,
            source="test",
        )

        batch1 = [md1]
        batch2 = [md2]

        result = check_idempotency(batch1, batch2)

        assert result is False, "Different content batches should fail idempotency"


class TestInvariantsMonotonicTimestamps:
    """Tests for monotonic timestamp invariant checking."""

    @pytest.mark.smoke
    def test_invariants_monotonic_pass(self):
        """Batch with increasing timestamps should pass monotonic check."""
        now = datetime.now(UTC)

        md1 = MarketData(
            symbol="AAPL",
            price=Decimal("175.43"),
            timestamp=now,
            volume=1000000,
            source="test",
        )
        md2 = MarketData(
            symbol="AAPL",
            price=Decimal("175.50"),
            timestamp=now + timedelta(seconds=10),
            volume=1000100,
            source="test",
        )
        md3 = MarketData(
            symbol="AAPL",
            price=Decimal("175.55"),
            timestamp=now + timedelta(seconds=20),
            volume=1000200,
            source="test",
        )

        batch = [md1, md2, md3]

        result = check_monotonic_timestamps(batch)

        assert result is True, "Increasing timestamps should pass monotonic check"

    def test_invariants_monotonic_equal_timestamps(self):
        """Batch with equal timestamps should pass monotonic check."""
        now = datetime.now(UTC)

        md1 = MarketData(
            symbol="AAPL",
            price=Decimal("175.43"),
            timestamp=now,
            volume=1000000,
            source="test",
        )
        md2 = MarketData(
            symbol="MSFT",
            price=Decimal("400.00"),
            timestamp=now,  # Same timestamp
            volume=500000,
            source="test",
        )

        batch = [md1, md2]

        result = check_monotonic_timestamps(batch)

        assert result is True, "Equal timestamps should pass monotonic check (ties allowed)"

    def test_invariants_monotonic_fail(self):
        """Batch with decreasing timestamp in middle should fail monotonic check."""
        now = datetime.now(UTC)

        md1 = MarketData(
            symbol="AAPL",
            price=Decimal("175.43"),
            timestamp=now,
            volume=1000000,
            source="test",
        )
        md2 = MarketData(
            symbol="AAPL",
            price=Decimal("175.50"),
            timestamp=now + timedelta(seconds=20),  # Jumps forward
            volume=1000100,
            source="test",
        )
        md3 = MarketData(
            symbol="AAPL",
            price=Decimal("175.55"),
            timestamp=now + timedelta(seconds=10),  # Goes backward!
            volume=1000200,
            source="test",
        )

        batch = [md1, md2, md3]

        result = check_monotonic_timestamps(batch)

        assert result is False, "Decreasing timestamp should fail monotonic check"

    def test_invariants_monotonic_empty_batch(self):
        """Empty batch should pass monotonic check."""
        result = check_monotonic_timestamps([])
        assert result is True, "Empty batch should pass monotonic check"

    def test_invariants_monotonic_single_item(self):
        """Single item batch should pass monotonic check."""
        md = MarketData(
            symbol="AAPL",
            price=Decimal("175.43"),
            timestamp=datetime.now(UTC),
            volume=1000000,
            source="test",
        )

        result = check_monotonic_timestamps([md])

        assert result is True, "Single item batch should pass monotonic check"


class TestInvariantsUniqueness:
    """Tests for uniqueness invariant checking."""

    @pytest.mark.smoke
    def test_invariants_uniqueness_pass(self):
        """Batch with unique trade_ids should pass uniqueness check."""
        now = datetime.now(UTC)

        td1 = TradeData(
            trade_id="TRD-001",
            client_id="CLIENT-001",
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("100"),
            price=Decimal("175.43"),
            timestamp=now,
            venue="NYSE",
        )
        td2 = TradeData(
            trade_id="TRD-002",
            client_id="CLIENT-001",
            symbol="AAPL",
            side="SELL",
            quantity=Decimal("50"),
            price=Decimal("176.00"),
            timestamp=now + timedelta(seconds=10),
            venue="NYSE",
        )
        td3 = TradeData(
            trade_id="TRD-003",
            client_id="CLIENT-001",
            symbol="MSFT",
            side="BUY",
            quantity=Decimal("25"),
            price=Decimal("400.00"),
            timestamp=now + timedelta(seconds=20),
            venue="NASDAQ",
        )

        batch = [td1, td2, td3]

        result = check_uniqueness(batch, key="trade_id", scope_key="client_id")

        assert result is True, "Unique trade_ids should pass uniqueness check"

    def test_invariants_uniqueness_fail(self):
        """Batch with duplicate trade_id should fail uniqueness check."""
        now = datetime.now(UTC)

        td1 = TradeData(
            trade_id="TRD-001",
            client_id="CLIENT-001",
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("100"),
            price=Decimal("175.43"),
            timestamp=now,
            venue="NYSE",
        )
        td2 = TradeData(
            trade_id="TRD-001",  # Duplicate trade_id!
            client_id="CLIENT-001",
            symbol="AAPL",
            side="SELL",
            quantity=Decimal("50"),
            price=Decimal("176.00"),
            timestamp=now + timedelta(seconds=10),
            venue="NYSE",
        )

        batch = [td1, td2]

        result = check_uniqueness(batch, key="trade_id", scope_key="client_id")

        assert result is False, "Duplicate trade_id should fail uniqueness check"

    def test_invariants_uniqueness_different_clients(self):
        """Same trade_id for different clients should pass (scoped uniqueness)."""
        now = datetime.now(UTC)

        td1 = TradeData(
            trade_id="TRD-001",
            client_id="CLIENT-001",
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("100"),
            price=Decimal("175.43"),
            timestamp=now,
            venue="NYSE",
        )
        td2 = TradeData(
            trade_id="TRD-001",  # Same trade_id but different client
            client_id="CLIENT-002",  # Different client
            symbol="AAPL",
            side="SELL",
            quantity=Decimal("50"),
            price=Decimal("176.00"),
            timestamp=now + timedelta(seconds=10),
            venue="NYSE",
        )

        batch = [td1, td2]

        result = check_uniqueness(batch, key="trade_id", scope_key="client_id")

        assert result is True, "Same trade_id for different clients should pass"

    def test_invariants_uniqueness_global(self):
        """Test global uniqueness (no scope)."""
        now = datetime.now(UTC)

        td1 = TradeData(
            trade_id="TRD-001",
            client_id="CLIENT-001",
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("100"),
            price=Decimal("175.43"),
            timestamp=now,
            venue="NYSE",
        )
        td2 = TradeData(
            trade_id="TRD-001",  # Duplicate globally
            client_id="CLIENT-002",
            symbol="AAPL",
            side="SELL",
            quantity=Decimal("50"),
            price=Decimal("176.00"),
            timestamp=now + timedelta(seconds=10),
            venue="NYSE",
        )

        batch = [td1, td2]

        # Without scope_key, should fail because trade_id duplicated globally
        result = check_uniqueness(batch, key="trade_id")

        assert result is False, "Duplicate trade_id globally should fail"


class TestInvariantsCompleteness:
    """Tests for batch completeness invariant checking."""

    def test_invariants_completeness_pass(self):
        """Non-empty batch with no nulls should pass completeness check."""
        md = MarketData(
            symbol="AAPL",
            price=Decimal("175.43"),
            timestamp=datetime.now(UTC),
            volume=1000000,
            source="test",
        )

        batch = [md, md]

        result = check_completeness(batch)

        assert result is True, "Complete batch should pass"

    def test_invariants_completeness_fail_empty(self):
        """Empty batch should fail completeness check."""
        result = check_completeness([])

        assert result is False, "Empty batch should fail completeness check"

    def test_invariants_completeness_fail_null(self):
        """Batch with null items should fail completeness check."""
        md = MarketData(
            symbol="AAPL",
            price=Decimal("175.43"),
            timestamp=datetime.now(UTC),
            volume=1000000,
            source="test",
        )

        batch = [md, None, md]

        result = check_completeness(batch)

        assert result is False, "Batch with None should fail completeness check"


class TestInvariantsReferentialIntegrity:
    """Tests for referential integrity invariant checking."""

    def test_invariants_referential_integrity_pass(self):
        """Trades with known symbols should pass referential integrity check."""
        now = datetime.now(UTC)

        td = TradeData(
            trade_id="TRD-001",
            client_id="CLIENT-001",
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("100"),
            price=Decimal("175.43"),
            timestamp=now,
            venue="NYSE",
        )

        known_symbols = {"AAPL", "MSFT", "GOOGL"}

        result = check_referential_integrity([td], known_symbols)

        assert result is True, "Trade with known symbol should pass"

    def test_invariants_referential_integrity_warning_mode(self):
        """Trades with unknown symbols should pass in warning mode (default)."""
        now = datetime.now(UTC)

        td = TradeData(
            trade_id="TRD-001",
            client_id="CLIENT-001",
            symbol="UNKNOWN",
            side="BUY",
            quantity=Decimal("100"),
            price=Decimal("175.43"),
            timestamp=now,
            venue="NYSE",
        )

        known_symbols = {"AAPL", "MSFT", "GOOGL"}

        result = check_referential_integrity([td], known_symbols, strict=False)

        assert result is True, "Warning mode should pass even with unknown symbol"

    def test_invariants_referential_integrity_strict_fail(self):
        """Trades with unknown symbols should fail in strict mode."""
        now = datetime.now(UTC)

        td = TradeData(
            trade_id="TRD-001",
            client_id="CLIENT-001",
            symbol="UNKNOWN",
            side="BUY",
            quantity=Decimal("100"),
            price=Decimal("175.43"),
            timestamp=now,
            venue="NYSE",
        )

        known_symbols = {"AAPL", "MSFT", "GOOGL"}

        result = check_referential_integrity([td], known_symbols, strict=True)

        assert result is False, "Strict mode should fail with unknown symbol"
