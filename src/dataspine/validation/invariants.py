"""
System invariant checking for dataspine.

This module implements invariant checking as defined in docs/invariants.md.
Invariants are system-wide properties that must hold true across batches
and operations.

Invariants Implemented:
    - Invariant 1: Idempotency
    - Invariant 2: Timestamp Ordering
    - Invariant 3: Batch Completeness
    - Invariant 4: Uniqueness
    - Invariant 5: Referential Integrity

Example Usage:
    >>> from dataspine.validation.invariants import (
    ...     check_idempotency,
    ...     check_monotonic_timestamps,
    ...     check_completeness,
    ...     check_uniqueness,
    ...     check_referential_integrity,
    ... )
    >>>
    >>> # Check if two batches are identical (idempotency)
    >>> is_idempotent = check_idempotency(batch1, batch2)
    >>>
    >>> # Check timestamp ordering
    >>> is_monotonic = check_monotonic_timestamps(batch)
"""

import logging
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


def check_idempotency(batch1: list[Any], batch2: list[Any]) -> bool:
    """
    Check Invariant 1: Idempotency.

    Verifies that processing the same input data twice produces identical output.
    Compares two batches element by element to ensure they are identical.

    Args:
        batch1: First batch of records to compare.
        batch2: Second batch of records to compare.

    Returns:
        True if batches are identical, False otherwise.

    Example:
        >>> batch1 = [MarketData(...), MarketData(...)]
        >>> batch2 = process(raw_data)  # First run
        >>> batch3 = process(raw_data)  # Second run
        >>> assert check_idempotency(batch2, batch3), "Processing is not idempotent!"
    """
    # Check length first
    if len(batch1) != len(batch2):
        logger.warning(
            "Idempotency violation: batch sizes differ",
            extra={
                "extra_fields": {
                    "batch1_size": len(batch1),
                    "batch2_size": len(batch2),
                    "difference": abs(len(batch1) - len(batch2)),
                }
            },
        )
        return False

    # Compare element by element
    differences: list[int] = []
    for i, (item1, item2) in enumerate(zip(batch1, batch2, strict=False)):
        if item1 != item2:
            differences.append(i)

    if differences:
        logger.warning(
            "Idempotency violation: batches differ at certain indices",
            extra={
                "extra_fields": {
                    "difference_count": len(differences),
                    "differing_indices": differences[:10],  # Limit to first 10
                    "total_records": len(batch1),
                }
            },
        )
        return False

    logger.debug(
        "Idempotency check passed",
        extra={
            "extra_fields": {
                "batch_size": len(batch1),
            }
        },
    )
    return True


def check_monotonic_timestamps(batch: list[Any]) -> bool:
    """
    Check Invariant 2: Timestamp Ordering.

    Verifies that timestamps within a batch are monotonically non-decreasing.
    For batch[i] and batch[i+1]: timestamp[i] <= timestamp[i+1].
    Ties (equal timestamps) are allowed.

    Args:
        batch: List of records with .timestamp attribute.

    Returns:
        True if timestamps are monotonically non-decreasing, False otherwise.

    Example:
        >>> sorted_batch = sorted(batch, key=lambda x: x.timestamp)
        >>> assert check_monotonic_timestamps(sorted_batch)
    """
    if len(batch) <= 1:
        logger.debug(
            "Monotonic timestamp check passed (trivial case)",
            extra={
                "extra_fields": {
                    "batch_size": len(batch),
                }
            },
        )
        return True

    violations: list[dict] = []

    for i in range(len(batch) - 1):
        current = batch[i]
        next_item = batch[i + 1]

        # Get timestamps
        current_ts = getattr(current, "timestamp", None)
        next_ts = getattr(next_item, "timestamp", None)

        if current_ts is None or next_ts is None:
            violations.append({
                "index": i,
                "reason": "missing timestamp attribute",
                "current_has_ts": current_ts is not None,
                "next_has_ts": next_ts is not None,
            })
            continue

        # Check monotonic (current <= next)
        if current_ts > next_ts:
            violations.append({
                "index": i,
                "reason": "timestamp decreased",
                "current_timestamp": current_ts.isoformat() if hasattr(current_ts, "isoformat") else str(current_ts),
                "next_timestamp": next_ts.isoformat() if hasattr(next_ts, "isoformat") else str(next_ts),
            })

    if violations:
        logger.warning(
            "Monotonic timestamp violation detected",
            extra={
                "extra_fields": {
                    "violation_count": len(violations),
                    "violations": violations[:10],  # Limit to first 10
                    "batch_size": len(batch),
                }
            },
        )
        return False

    logger.debug(
        "Monotonic timestamp check passed",
        extra={
            "extra_fields": {
                "batch_size": len(batch),
            }
        },
    )
    return True


def check_completeness(batch: list[Any]) -> bool:
    """
    Check Invariant 3: Batch Completeness.

    Verifies that a batch is complete:
    - Batch is not empty
    - All items in batch are non-null

    Args:
        batch: List of records to check.

    Returns:
        True if batch is complete, False otherwise.

    Example:
        >>> batch = [record1, record2, record3]
        >>> assert check_completeness(batch), "Batch is incomplete!"
    """
    # Check not empty
    if not batch:
        logger.warning(
            "Completeness violation: batch is empty",
            extra={
                "extra_fields": {
                    "batch_size": 0,
                }
            },
        )
        return False

    # Check all items are non-null
    null_indices: list[int] = []
    for i, item in enumerate(batch):
        if item is None:
            null_indices.append(i)

    if null_indices:
        logger.warning(
            "Completeness violation: batch contains null items",
            extra={
                "extra_fields": {
                    "null_count": len(null_indices),
                    "null_indices": null_indices[:10],  # Limit to first 10
                    "batch_size": len(batch),
                }
            },
        )
        return False

    logger.debug(
        "Completeness check passed",
        extra={
            "extra_fields": {
                "batch_size": len(batch),
            }
        },
    )
    return True


def check_uniqueness(
    records: list[Any],
    key: str = "trade_id",
    scope_key: str | None = None,
) -> bool:
    """
    Check Invariant 4: Uniqueness.

    Verifies that certain fields are unique within their scope.
    For trade data, trade_id must be unique within client_id scope.

    Args:
        records: List of records to check.
        key: The field name to check for uniqueness (default: "trade_id").
        scope_key: Optional field name for scoping uniqueness (e.g., "client_id").
                   If provided, uniqueness is checked within each scope value.

    Returns:
        True if all key values are unique within their scope, False if duplicates found.

    Example:
        >>> # Check trade_id uniqueness within client_id scope
        >>> assert check_uniqueness(trades, key="trade_id", scope_key="client_id")
        >>>
        >>> # Check global uniqueness
        >>> assert check_uniqueness(records, key="id")
    """
    if not records:
        logger.debug(
            "Uniqueness check passed (empty batch)",
            extra={
                "extra_fields": {
                    "key": key,
                    "scope_key": scope_key,
                }
            },
        )
        return True

    # Track seen values: {scope: {key_value: [indices]}}
    seen: dict[Any, dict[Any, list[int]]] = defaultdict(lambda: defaultdict(list))
    duplicates: list[dict] = []

    for i, record in enumerate(records):
        key_value = getattr(record, key, None)
        if key_value is None:
            continue  # Skip records without the key field

        # Determine scope
        if scope_key:
            scope_value = getattr(record, scope_key, None)
        else:
            scope_value = "__global__"

        # Check if already seen
        if key_value in seen[scope_value]:
            # This is a duplicate
            duplicates.append({
                "key": key,
                "key_value": str(key_value),
                "scope_key": scope_key,
                "scope_value": str(scope_value) if scope_value != "__global__" else None,
                "indices": [*seen[scope_value][key_value], i],
            })

        seen[scope_value][key_value].append(i)

    if duplicates:
        logger.warning(
            "Uniqueness violation: duplicate keys found",
            extra={
                "extra_fields": {
                    "duplicate_count": len(duplicates),
                    "duplicates": duplicates[:10],  # Limit to first 10
                    "key": key,
                    "scope_key": scope_key,
                    "total_records": len(records),
                }
            },
        )
        return False

    logger.debug(
        "Uniqueness check passed",
        extra={
            "extra_fields": {
                "key": key,
                "scope_key": scope_key,
                "total_records": len(records),
            }
        },
    )
    return True


def check_referential_integrity(
    trades: list[Any],
    known_symbols: set[str],
    strict: bool = False,
) -> bool:
    """
    Check Invariant 5: Referential Integrity.

    Verifies that trade symbols exist in the market data universe.
    By default, logs a warning for unknown symbols but returns True.
    Set strict=True to return False when unknown symbols are found.

    Args:
        trades: List of trade records with .symbol attribute.
        known_symbols: Set of valid symbols from market data.
        strict: If True, return False when unknown symbols found.
                If False (default), log warning but return True.

    Returns:
        True if all symbols are known (or strict=False and only warnings).
        False only if strict=True and unknown symbols are found.

    Example:
        >>> known_symbols = {"AAPL", "MSFT", "GOOGL"}
        >>> trades = [TradeData(symbol="AAPL", ...), TradeData(symbol="UNKNOWN", ...)]
        >>> # Warning mode (default)
        >>> check_referential_integrity(trades, known_symbols)  # Returns True, logs warning
        >>> # Strict mode
        >>> check_referential_integrity(trades, known_symbols, strict=True)  # Returns False
    """
    if not trades:
        logger.debug(
            "Referential integrity check passed (no trades)",
            extra={
                "extra_fields": {
                    "known_symbols_count": len(known_symbols),
                }
            },
        )
        return True

    unknown_symbols: dict[str, list[int]] = defaultdict(list)

    for i, trade in enumerate(trades):
        symbol = getattr(trade, "symbol", None)
        if symbol is None:
            continue

        if symbol not in known_symbols:
            unknown_symbols[symbol].append(i)

    if unknown_symbols:
        log_level = logging.WARNING if not strict else logging.ERROR
        logger.log(
            log_level,
            "Referential integrity: unknown symbols found in trades",
            extra={
                "extra_fields": {
                    "unknown_symbol_count": len(unknown_symbols),
                    "unknown_symbols": list(unknown_symbols.keys())[:20],  # Limit
                    "affected_trade_count": sum(len(v) for v in unknown_symbols.values()),
                    "total_trades": len(trades),
                    "known_symbols_count": len(known_symbols),
                    "strict_mode": strict,
                }
            },
        )

        if strict:
            return False

    logger.debug(
        "Referential integrity check passed",
        extra={
            "extra_fields": {
                "total_trades": len(trades),
                "known_symbols_count": len(known_symbols),
            }
        },
    )
    return True
