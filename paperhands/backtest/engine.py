"""Backtesting engine."""

from datetime import datetime, timedelta
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
        timeframe: str = "1Day",
        warmup_days: int = 0
    ):
        """
        Initialize backtest engine.

        Args:
            strategy: Strategy to backtest
            data_provider: Data provider for historical data
            symbols: List of symbols to trade
            start_date: Backtest start date (when trading/tracking begins)
            end_date: Backtest end date
            initial_cash: Starting cash
            commission_per_share: Commission per share
            slippage_percent: Slippage percentage
            timeframe: Bar timeframe (e.g., "1Hour", "1Day")
            warmup_days: Number of days of historical data to load before start_date
                        for indicator warmup (e.g., 365 for strategies needing 1 year lookback)
        """
        self.strategy = strategy
        self.data_provider = data_provider
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.timeframe = timeframe
        self.warmup_days = warmup_days

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

        # Calculate data fetch start date (includes warmup period)
        if self.warmup_days > 0:
            data_start_date = self.start_date - timedelta(days=self.warmup_days)
            print(f"Including {self.warmup_days} days warmup period (fetching from {data_start_date.date()})")
        else:
            data_start_date = self.start_date

        # Load data for all symbols (including warmup period)
        bars_dict = self.data_provider.get_bars_multi(
            self.symbols,
            data_start_date,
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

        # Separate warmup and live trading periods
        warmup_timestamps = [ts for ts in timestamps if ts < self.start_date]
        live_timestamps = [ts for ts in timestamps if ts >= self.start_date]

        # Process warmup period (feed bars to strategy but don't track equity or allow trading)
        if warmup_timestamps:
            if verbose:
                print(f"Processing {len(warmup_timestamps)} warmup bars...")
            self.broker.disable_trading()  # Prevent orders during warmup
            for timestamp in warmup_timestamps:
                self.context.current_time = timestamp
                bars = self.bars_by_time[timestamp]
                for symbol, bar in bars.items():
                    self.strategy.on_bar(bar)
            self.broker.enable_trading()  # Re-enable trading for live period

        # Progress bar for live trading period
        iterator = tqdm(live_timestamps, desc="Backtesting") if verbose else live_timestamps

        # Run through each timestamp (live trading period)
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

    def plot_portfolio(self, benchmark: str = None, show: bool = True):
        """
        Plot portfolio equity curve with buy/sell trade markers.

        Best for multi-symbol strategies where plotting a single stock
        price doesn't make sense.

        Args:
            benchmark: Optional benchmark symbol (e.g., "SPY") to compare against.
                      Will be normalized to start at the same value as initial cash.
            show: Whether to call plt.show() (set False if you want to customize further)

        Returns:
            matplotlib figure and axes (fig, ax)
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
        except ImportError:
            print("matplotlib is required for plotting. Install with: pip install matplotlib")
            return None

        # Get equity curve
        equity_df = self.get_equity_curve()
        if equity_df.empty:
            print("No equity data available")
            return None

        # Get all trades
        trades_df = self.get_trades()

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 7))

        # Plot equity curve
        ax.plot(equity_df.index, equity_df['equity'], label='Portfolio', color='#2962FF', linewidth=1.5)

        # Fill profit/loss areas
        ax.fill_between(
            equity_df.index,
            self.portfolio.initial_cash,
            equity_df['equity'],
            where=(equity_df['equity'] >= self.portfolio.initial_cash),
            alpha=0.3, color='#00C853', interpolate=True, label='Profit'
        )
        ax.fill_between(
            equity_df.index,
            self.portfolio.initial_cash,
            equity_df['equity'],
            where=(equity_df['equity'] < self.portfolio.initial_cash),
            alpha=0.3, color='#FF1744', interpolate=True, label='Loss'
        )

        # Initial cash line
        ax.axhline(y=self.portfolio.initial_cash, color='gray', linestyle='--', alpha=0.5, label='Initial Cash')

        # Plot benchmark if provided
        benchmark_return = None
        if benchmark:
            try:
                benchmark_bars = self.data_provider.get_bars(
                    benchmark, self.start_date, self.end_date, self.timeframe
                )
                if benchmark_bars:
                    benchmark_df = pd.DataFrame([
                        {'timestamp': bar.timestamp, 'close': bar.close}
                        for bar in benchmark_bars
                    ])
                    benchmark_df.set_index('timestamp', inplace=True)

                    # Normalize benchmark to start at initial cash value
                    initial_benchmark_price = benchmark_df['close'].iloc[0]
                    benchmark_df['normalized'] = (
                        benchmark_df['close'] / initial_benchmark_price * self.portfolio.initial_cash
                    )

                    ax.plot(
                        benchmark_df.index,
                        benchmark_df['normalized'],
                        label=f'{benchmark} (Buy & Hold)',
                        color='#FF9800',
                        linewidth=1.5,
                        linestyle='--',
                        alpha=0.8
                    )

                    # Calculate benchmark return for summary
                    benchmark_return = (
                        (benchmark_df['close'].iloc[-1] - initial_benchmark_price)
                        / initial_benchmark_price * 100
                    )
            except Exception as e:
                print(f"Could not load benchmark {benchmark}: {e}")

        # Plot buy/sell markers on the equity curve
        if not trades_df.empty:
            # Map trade timestamps to equity values
            buys = trades_df[trades_df['side'] == 'buy'].copy()
            sells = trades_df[trades_df['side'] == 'sell'].copy()

            if not buys.empty:
                buy_times = pd.to_datetime(buys['timestamp'])
                # Get equity values at buy times (use portfolio_value from trades if available)
                if 'portfolio_value' in buys.columns:
                    buy_values = buys['portfolio_value'].values
                else:
                    buy_values = buys['cash_after'].values
                ax.scatter(
                    buy_times,
                    buy_values,
                    marker='^',
                    color='#00C853',
                    s=60,
                    label='Buy',
                    zorder=5,
                    edgecolors='white',
                    linewidths=0.5,
                    alpha=0.8
                )

            if not sells.empty:
                sell_times = pd.to_datetime(sells['timestamp'])
                if 'portfolio_value' in sells.columns:
                    sell_values = sells['portfolio_value'].values
                else:
                    sell_values = sells['cash_after'].values
                ax.scatter(
                    sell_times,
                    sell_values,
                    marker='v',
                    color='#FF1744',
                    s=60,
                    label='Sell',
                    zorder=5,
                    edgecolors='white',
                    linewidths=0.5,
                    alpha=0.8
                )

        ax.set_ylabel('Portfolio Value ($)', fontsize=11)
        ax.set_xlabel('Date', fontsize=11)
        ax.set_title(f'Portfolio Performance - {len(self.symbols)} symbols', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)

        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45)

        # Add summary text
        if self.analytics:
            metrics = self.analytics.calculate_metrics()
            summary_parts = [
                f"Return: {metrics['total_return_percent']:.1f}%",
            ]
            if benchmark_return is not None:
                summary_parts.append(f"{benchmark}: {benchmark_return:.1f}%")
            summary_parts.extend([
                f"Sharpe: {metrics['sharpe_ratio']:.2f}",
                f"Max DD: {metrics['max_drawdown']:.1f}%",
                f"Win Rate: {metrics['win_rate']:.1f}%",
                f"Trades: {metrics['total_trades']}",
            ])
            summary_text = " | ".join(summary_parts)
            ax.text(
                0.5, -0.12, summary_text,
                transform=ax.transAxes,
                fontsize=10,
                ha='center',
                color='gray'
            )

        plt.tight_layout()

        if show:
            plt.show()

        return fig, ax
