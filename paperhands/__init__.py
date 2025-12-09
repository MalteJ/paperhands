"""
Paperhands - A backtesting framework for stock and options trading strategies.

This framework allows you to develop trading strategies that can be seamlessly
moved between backtesting and live trading environments.
"""

__version__ = "0.1.0"

# Core types
from paperhands.core.types import (
    Bar,
    Order,
    OrderType,
    OrderSide,
    OrderStatus,
    TimeInForce,
    Position,
    Asset,
    AssetType,
)
from paperhands.core.events import Event, BarEvent, OrderEvent, FillEvent

# Strategy
from paperhands.strategy.base import Strategy
from paperhands.strategy.context import StrategyContext

# Backtest
from paperhands.backtest.engine import BacktestEngine
from paperhands.backtest.analytics import PerformanceAnalytics

# Data providers
from paperhands.data.provider import DataProvider
from paperhands.data.yahoo_provider import YahooDataProvider
from paperhands.data.alpaca_provider import AlpacaDataProvider
from paperhands.data.eodhd_provider import EODHDProvider
from paperhands.data.cached_provider import CachedDataProvider

# Execution
from paperhands.execution.broker import Broker
from paperhands.execution.backtest_broker import BacktestBroker

# Portfolio
from paperhands.portfolio.portfolio import Portfolio

__all__ = [
    # Version
    "__version__",
    # Core types
    "Bar",
    "Order",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "TimeInForce",
    "Position",
    "Asset",
    "AssetType",
    # Events
    "Event",
    "BarEvent",
    "OrderEvent",
    "FillEvent",
    # Strategy
    "Strategy",
    "StrategyContext",
    # Backtest
    "BacktestEngine",
    "PerformanceAnalytics",
    # Data providers
    "DataProvider",
    "YahooDataProvider",
    "AlpacaDataProvider",
    "EODHDProvider",
    "CachedDataProvider",
    # Execution
    "Broker",
    "BacktestBroker",
    # Portfolio
    "Portfolio",
]
