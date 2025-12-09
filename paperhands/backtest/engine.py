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

    def plot_trades(self, symbol: Optional[str] = None, show: bool = True):
        """
        Plot price chart with buy/sell trade markers.

        Args:
            symbol: Symbol to plot. If None, uses first symbol in symbols list.
            show: Whether to call plt.show() (set False if you want to customize further)

        Returns:
            matplotlib figure and axes tuple (fig, (ax1, ax2))
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
        except ImportError:
            print("matplotlib is required for plotting. Install with: pip install matplotlib")
            return None

        # Default to first symbol if not specified
        if symbol is None:
            symbol = self.symbols[0]

        if symbol not in self.symbols:
            print(f"Symbol {symbol} not in backtest symbols: {self.symbols}")
            return None

        # Get price data for the symbol
        prices = []
        for timestamp in sorted(self.bars_by_time.keys()):
            if symbol in self.bars_by_time[timestamp]:
                bar = self.bars_by_time[timestamp][symbol]
                prices.append({
                    'timestamp': timestamp,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close
                })

        if not prices:
            print(f"No price data for {symbol}")
            return None

        price_df = pd.DataFrame(prices)
        price_df.set_index('timestamp', inplace=True)

        # Get trades for this symbol
        trades_df = self.get_trades()
        if not trades_df.empty:
            trades_df = trades_df[trades_df['symbol'] == symbol].copy()

        # Create figure with two subplots: price chart and equity curve
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[2, 1], sharex=True)

        # Plot price line
        ax1.plot(price_df.index, price_df['close'], label=f'{symbol} Close', color='#2962FF', linewidth=1.5)
        ax1.fill_between(price_df.index, price_df['low'], price_df['high'], alpha=0.1, color='#2962FF')

        # Plot buy/sell markers
        if not trades_df.empty:
            buys = trades_df[trades_df['side'] == 'buy']
            sells = trades_df[trades_df['side'] == 'sell']

            if not buys.empty:
                ax1.scatter(
                    pd.to_datetime(buys['timestamp']),
                    buys['price'],
                    marker='^',
                    color='#00C853',
                    s=100,
                    label='Buy',
                    zorder=5,
                    edgecolors='white',
                    linewidths=1
                )

            if not sells.empty:
                ax1.scatter(
                    pd.to_datetime(sells['timestamp']),
                    sells['price'],
                    marker='v',
                    color='#FF1744',
                    s=100,
                    label='Sell',
                    zorder=5,
                    edgecolors='white',
                    linewidths=1
                )

        ax1.set_ylabel('Price ($)', fontsize=11)
        ax1.set_title(f'{symbol} - Backtest Results', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)

        # Plot equity curve
        equity_df = self.get_equity_curve()
        if not equity_df.empty:
            ax2.plot(equity_df.index, equity_df['equity'], label='Portfolio Value', color='#7C4DFF', linewidth=1.5)
            ax2.fill_between(equity_df.index, self.portfolio.initial_cash, equity_df['equity'],
                           where=(equity_df['equity'] >= self.portfolio.initial_cash),
                           alpha=0.3, color='#00C853', interpolate=True)
            ax2.fill_between(equity_df.index, self.portfolio.initial_cash, equity_df['equity'],
                           where=(equity_df['equity'] < self.portfolio.initial_cash),
                           alpha=0.3, color='#FF1744', interpolate=True)
            ax2.axhline(y=self.portfolio.initial_cash, color='gray', linestyle='--', alpha=0.5, label='Initial Cash')

        ax2.set_ylabel('Portfolio Value ($)', fontsize=11)
        ax2.set_xlabel('Date', fontsize=11)
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)

        # Format x-axis dates
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45)

        # Add summary text
        if self.analytics:
            metrics = self.analytics.calculate_metrics()
            summary_text = (
                f"Return: {metrics['total_return_percent']:.1f}% | "
                f"Sharpe: {metrics['sharpe_ratio']:.2f} | "
                f"Max DD: {metrics['max_drawdown']:.1f}% | "
                f"Win Rate: {metrics['win_rate']:.1f}% | "
                f"Trades: {metrics['total_trades']}"
            )
            fig.suptitle(summary_text, fontsize=10, y=0.02, color='gray')

        plt.tight_layout()

        if show:
            plt.show()

        return fig, (ax1, ax2)
