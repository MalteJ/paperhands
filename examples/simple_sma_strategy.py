"""
Simple Moving Average Crossover Strategy

This example demonstrates how to build a basic strategy using the framework.
The strategy buys when the short-term SMA crosses above the long-term SMA,
and sells when it crosses below.

This exact same strategy code can be used for both backtesting and live trading.
"""

from datetime import datetime, timedelta
from src.strategy.base import Strategy
from src.core.types import Bar
from src.data.yahoo_provider import YahooDataProvider
from src.backtest.engine import BacktestEngine


class SMAStrategy(Strategy):
    """Simple Moving Average Crossover Strategy."""

    def __init__(self, symbol: str, short_window: int = 20, long_window: int = 50,
                 position_size: float = 0.95):
        """
        Initialize strategy.

        Args:
            symbol: Symbol to trade
            short_window: Short SMA window
            long_window: Long SMA window
            position_size: Fraction of portfolio to use per trade
        """
        super().__init__(name=f"SMA_{short_window}_{long_window}")
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        self.position_size = position_size

        # Track recent closes for SMA calculation
        self.closes = []

    def on_start(self):
        """Called when strategy starts."""
        print(f"Starting {self.name} for {self.symbol}")
        print(f"Short SMA: {self.short_window}, Long SMA: {self.long_window}")

    def on_bar(self, bar: Bar):
        """Process each bar."""
        # Only process bars for our symbol
        if bar.symbol != self.symbol:
            return

        # Add close price to our history
        self.closes.append(bar.close)

        # Need enough data for long SMA
        if len(self.closes) < self.long_window:
            return

        # Keep only what we need
        if len(self.closes) > self.long_window:
            self.closes = self.closes[-self.long_window:]

        # Calculate SMAs
        short_sma = sum(self.closes[-self.short_window:]) / self.short_window
        long_sma = sum(self.closes[-self.long_window:]) / self.long_window

        # Get current position
        position = self.context.get_position(self.symbol)
        current_position = position.quantity if position else 0

        # Trading logic
        if short_sma > long_sma and current_position == 0:
            # Buy signal - short SMA crossed above long SMA
            available_cash = self.context.cash * self.position_size
            shares = int(available_cash / bar.close)

            if shares > 0:
                print(f"{bar.timestamp}: BUY {shares} shares at ${bar.close:.2f}")
                print(f"  Short SMA: ${short_sma:.2f}, Long SMA: ${long_sma:.2f}")
                self.context.buy(self.symbol, shares)

        elif short_sma < long_sma and current_position > 0:
            # Sell signal - short SMA crossed below long SMA
            print(f"{bar.timestamp}: SELL {current_position} shares at ${bar.close:.2f}")
            print(f"  Short SMA: ${short_sma:.2f}, Long SMA: ${long_sma:.2f}")
            self.context.sell(self.symbol, current_position)

    def on_stop(self):
        """Called when strategy stops."""
        print(f"\n{self.name} completed")

        # Close any open positions
        position = self.context.get_position(self.symbol)
        if position and position.quantity > 0:
            print(f"Closing final position of {position.quantity} shares")


if __name__ == "__main__":
    # Example: Backtest the strategy

    # Set up parameters
    symbol = "SPY"
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()

    # Create data provider (using Yahoo Finance - free)
    data_provider = YahooDataProvider()

    # Create strategy
    strategy = SMAStrategy(symbol=symbol, short_window=20, long_window=50)

    # Create backtest engine
    engine = BacktestEngine(
        strategy=strategy,
        data_provider=data_provider,
        symbols=[symbol],
        start_date=start_date,
        end_date=end_date,
        initial_cash=100000.0,
        timeframe="1Day"
    )

    # Run backtest
    print("="*60)
    print(f"Backtesting {symbol} from {start_date.date()} to {end_date.date()}")
    print("="*60)

    analytics = engine.run(verbose=True)

    # Print detailed report
    print("\n" + analytics.generate_report())

    # Get equity curve
    equity = engine.get_equity_curve()
    print(f"\nEquity curve has {len(equity)} data points")

    # Get trades
    trades = engine.get_trades()
    if not trades.empty:
        print(f"\nTrade History:")
        print(trades.to_string())
