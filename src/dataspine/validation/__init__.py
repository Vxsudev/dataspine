"""
Data validation for dataspine.

This module exports contract validation and invariant checking functionality:
- ContractValidator: Validates data against defined contracts
- Invariant checking functions for system-wide properties

Example:
    >>> from dataspine.validation import ContractValidator
    >>> from dataspine.validation import (
    ...     check_idempotency,
    ...     check_monotonic_timestamps,
    ...     check_completeness,
    ...     check_uniqueness,
    ...     check_referential_integrity,
    ... )
"""

from dataspine.validation.contracts import ContractValidator
from dataspine.validation.invariants import (
    check_completeness,
    check_idempotency,
    check_monotonic_timestamps,
    check_referential_integrity,
    check_uniqueness,
)

__all__ = [
    "ContractValidator",
    "check_idempotency",
    "check_monotonic_timestamps",
    "check_completeness",
    "check_uniqueness",
    "check_referential_integrity",
]
