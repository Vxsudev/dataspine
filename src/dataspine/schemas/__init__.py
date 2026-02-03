"""
Data schemas for dataspine.

This module exports the canonical schemas used for normalized data:
- MarketData: Market price and volume data
- TradeData: Trade execution data

Example:
    >>> from dataspine.schemas import MarketData, TradeData
"""

from dataspine.schemas.market_data import MarketData
from dataspine.schemas.trade_data import TradeData

__all__ = ["MarketData", "TradeData"]
