"""Base strategy class."""

from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd

from .context import StrategyContext
from ..core.types import Bar
from ..core.events import BarEvent, FillEvent


class Strategy(ABC):
    """
    Base class for all trading strategies.

    Strategies inherit from this class and implement the required methods.
    The same strategy code works in both backtesting and live trading.

    Key design principle: Strategies only interact with the StrategyContext,
    never directly with brokers, portfolios, or data providers. This ensures
    portability between backtesting and live trading.
    """

    def __init__(self, name: str = None):
        """
        Initialize strategy.

        Args:
            name: Strategy name (defaults to class name)
        """
        self.name = name or self.__class__.__name__
        self.context: Optional[StrategyContext] = None

    def set_context(self, context: StrategyContext):
        """
        Set the strategy context.

        This is called by the backtesting engine or live runner.

        Args:
            context: Strategy context
        """
        self.context = context

    @abstractmethod
    def on_start(self):
        """
        Called once when the strategy starts.

        Use this to initialize state, load parameters, etc.
        """
        pass

    @abstractmethod
    def on_bar(self, bar: Bar):
        """
        Called on each new bar.

        This is the main strategy logic. Implement your trading decisions here.

        Args:
            bar: The new price bar
        """
        pass

    def on_fill(self, fill_event: FillEvent):
        """
        Called when an order is filled.

        Override this if you need to react to fills (e.g., placing stop losses).

        Args:
            fill_event: Fill event with details
        """
        pass

    def on_stop(self):
        """
        Called when the strategy stops.

        Use this for cleanup, final reporting, etc.
        """
        pass

    # ========== Vectorized strategy support ==========

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Perform vectorized analysis on historical data.

        This is optional and allows for hybrid strategies that use
        vectorized operations for backtesting but event-driven logic
        for live trading.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with additional columns (signals, indicators, etc.)
        """
        return df

    def should_enter_long(self, bar: Bar, analysis: Optional[pd.DataFrame] = None) -> bool:
        """
        Check if strategy should enter a long position.

        Override this for simple signal-based strategies.

        Args:
            bar: Current bar
            analysis: Optional pre-computed analysis

        Returns:
            True if should enter long
        """
        return False

    def should_exit_long(self, bar: Bar, analysis: Optional[pd.DataFrame] = None) -> bool:
        """
        Check if strategy should exit a long position.

        Override this for simple signal-based strategies.

        Args:
            bar: Current bar
            analysis: Optional pre-computed analysis

        Returns:
            True if should exit long
        """
        return False

    def should_enter_short(self, bar: Bar, analysis: Optional[pd.DataFrame] = None) -> bool:
        """
        Check if strategy should enter a short position.

        Override this for simple signal-based strategies.

        Args:
            bar: Current bar
            analysis: Optional pre-computed analysis

        Returns:
            True if should enter short
        """
        return False

    def should_exit_short(self, bar: Bar, analysis: Optional[pd.DataFrame] = None) -> bool:
        """
        Check if strategy should exit a short position.

        Override this for simple signal-based strategies.

        Args:
            bar: Current bar
            analysis: Optional pre-computed analysis

        Returns:
            True if should exit short
        """
        return False
