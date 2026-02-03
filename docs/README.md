# Dataspine Documentation

This directory contains comprehensive data contract documentation for the dataspine project.

## Documentation Files

### 1. [source_registry.md](source_registry.md)
Registry of all external data sources, including:
- Market data sources (IEX Cloud, Polygon.io)
- Trade data sources (Execution Feed CSV)
- API endpoints, field definitions, and authentication requirements

### 2. [canonical_schemas.md](canonical_schemas.md)
Normalized schemas that all data must conform to:
- **MarketData Schema**: Market price and volume data
- **TradeData Schema**: Trade execution data
- Field definitions, constraints, and examples

### 3. [contracts.md](contracts.md)
Validation rules enforced on all data:
- Required fields contract
- Price validity contract
- Timestamp validity contract
- Symbol format contract
- Trade-specific rules

### 4. [invariants.md](invariants.md)
System-wide properties that must hold true:
- Idempotency
- Timestamp ordering
- Batch completeness
- Uniqueness constraints
- Referential integrity

## Usage

These documents serve as the single source of truth for:
- Adapter implementations (use source_registry.md)
- Schema definitions (use canonical_schemas.md)
- Validation logic (use contracts.md)
- System testing (use invariants.md)

## Updates

When adding new data sources or modifying schemas:
1. Update the relevant documentation file first
2. Implement the code changes
3. Ensure validation tests cover the new contracts
4. Update this README if adding new documentation files
