"""Backtesting engine."""

from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from tqdm import tqdm

from ..strategy.base import Strategy
from ..strategy.context import StrategyContext
from ..data.provider import DataProvider
from ..portfolio.portfolio import Portfolio
from ..execution.backtest_broker import BacktestBroker
from ..core.types import Bar
from ..core.events import BarEvent
from .analytics import PerformanceAnalytics


class BacktestEngine:
    """
    Backtesting engine for running strategies on historical data.

    The engine orchestrates the backtest by:
    1. Loading historical data
    2. Creating portfolio and broker
    3. Running the strategy on each bar
    4. Processing orders and fills
    5. Tracking performance
    """

    def __init__(
        self,
        strategy: Strategy,
        data_provider: DataProvider,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        initial_cash: float = 100000.0,
        commission_per_share: float = 0.0,
        slippage_percent: float = 0.0,
        timeframe: str = "1Day"
    ):
        """
        Initialize backtest engine.

        Args:
            strategy: Strategy to backtest
            data_provider: Data provider for historical data
            symbols: List of symbols to trade
            start_date: Backtest start date
            end_date: Backtest end date
            initial_cash: Starting cash
            commission_per_share: Commission per share
            slippage_percent: Slippage percentage
            timeframe: Bar timeframe (e.g., "1Hour", "1Day")
        """
        self.strategy = strategy
        self.data_provider = data_provider
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.timeframe = timeframe

        # Initialize portfolio and broker
        self.portfolio = Portfolio(initial_cash=initial_cash)
        self.broker = BacktestBroker(
            portfolio=self.portfolio,
            commission_per_share=commission_per_share,
            slippage_percent=slippage_percent
        )

        # Create context and set it on strategy
        self.context = StrategyContext(
            broker=self.broker,
            portfolio=self.portfolio,
            data_provider=data_provider
        )
        self.strategy.set_context(self.context)

        # Track bars by timestamp for synchronization
        self.bars_by_time: Dict[datetime, Dict[str, Bar]] = {}

        # Analytics
        self.analytics: Optional[PerformanceAnalytics] = None

    def load_data(self):
        """Load historical data for all symbols."""
        print(f"Loading data for {len(self.symbols)} symbols...")

        # Load data for all symbols
        bars_dict = self.data_provider.get_bars_multi(
            self.symbols,
            self.start_date,
            self.end_date,
            self.timeframe
        )

        # Organize bars by timestamp
        for symbol, bars in bars_dict.items():
            for bar in bars:
                if bar.timestamp not in self.bars_by_time:
                    self.bars_by_time[bar.timestamp] = {}
                self.bars_by_time[bar.timestamp][symbol] = bar

        print(f"Loaded {len(self.bars_by_time)} bars")

    def run(self, verbose: bool = True) -> PerformanceAnalytics:
        """
        Run the backtest.

        Args:
            verbose: Show progress bar

        Returns:
            Performance analytics
        """
        # Load data
        self.load_data()

        if not self.bars_by_time:
            raise ValueError("No data loaded for backtest")

        # Call strategy on_start
        self.strategy.on_start()

        # Get sorted timestamps
        timestamps = sorted(self.bars_by_time.keys())

        # Progress bar
        iterator = tqdm(timestamps, desc="Backtesting") if verbose else timestamps

        # Run through each timestamp
        for timestamp in iterator:
            self.context.current_time = timestamp
            bars = self.bars_by_time[timestamp]

            # Update position prices
            prices = {symbol: bar.close for symbol, bar in bars.items()}
            self.portfolio.update_position_prices(prices, timestamp)

            # Process each bar through broker (check for fills)
            for symbol, bar in bars.items():
                # Check for order fills
                self.broker.process_bar(
                    symbol=symbol,
                    bar_open=bar.open,
                    bar_high=bar.high,
                    bar_low=bar.low,
                    bar_close=bar.close,
                    timestamp=timestamp
                )

                # Call strategy for this bar
                self.strategy.on_bar(bar)

            # Process fill events
            fill_events = self.broker.get_fill_events()
            for fill_event in fill_events:
                self.strategy.on_fill(fill_event)

        # Call strategy on_stop
        self.strategy.on_stop()

        # Generate analytics
        self.analytics = PerformanceAnalytics(self.portfolio)

        if verbose:
            print("\n" + "="*60)
            print("BACKTEST COMPLETE")
            print("="*60)
            self.print_summary()

        return self.analytics

    def print_summary(self):
        """Print backtest summary."""
        if not self.analytics:
            print("No analytics available. Run backtest first.")
            return

        summary = self.portfolio.summary()

        print(f"\nPortfolio Summary:")
        print(f"  Initial Cash:     ${summary['portfolio_value']:,.2f}")
        print(f"  Final Value:      ${self.portfolio.portfolio_value:,.2f}")
        print(f"  Total Return:     {summary['return_percent']:.2f}%")
        print(f"  Total P&L:        ${summary['total_pnl']:,.2f}")
        print(f"  Realized P&L:     ${summary['realized_pnl']:,.2f}")
        print(f"  Unrealized P&L:   ${summary['unrealized_pnl']:,.2f}")

        metrics = self.analytics.calculate_metrics()
        print(f"\nPerformance Metrics:")
        print(f"  Sharpe Ratio:     {metrics['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown:     {metrics['max_drawdown']:.2f}%")
        print(f"  Win Rate:         {metrics['win_rate']:.2f}%")
        print(f"  Total Trades:     {metrics['total_trades']}")
        print(f"  Avg Trade:        ${metrics['avg_trade_pnl']:,.2f}")

    def get_equity_curve(self) -> pd.DataFrame:
        """
        Get equity curve as DataFrame.

        Returns:
            DataFrame with timestamp and equity
        """
        if not self.portfolio.equity_history:
            return pd.DataFrame(columns=['timestamp', 'equity'])

        df = pd.DataFrame(
            self.portfolio.equity_history,
            columns=['timestamp', 'equity']
        )
        df.set_index('timestamp', inplace=True)
        return df

    def get_trades(self) -> pd.DataFrame:
        """
        Get trade history as DataFrame.

        Returns:
            DataFrame with trade details
        """
        if not self.portfolio.trade_history:
            return pd.DataFrame()

        return pd.DataFrame(self.portfolio.trade_history)
