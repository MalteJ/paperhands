"""
EODHD Data Provider Example

This example shows how to use the EODHD data provider for backtesting.
EODHD provides high-quality historical data with good US market coverage.

Make sure you have your EODHD_API_KEY in your .env file.
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.strategy.base import Strategy
from src.core.types import Bar
from src.data.eodhd_provider import EODHDProvider
from src.backtest.engine import BacktestEngine


# Load environment variables from .env file
load_dotenv()


class SimpleBreakoutStrategy(Strategy):
    """
    Simple breakout strategy that buys when price breaks above 20-day high.

    This demonstrates using EODHD data for backtesting.
    """

    def __init__(self, symbol: str, lookback: int = 20, position_size: float = 0.95):
        """
        Initialize strategy.

        Args:
            symbol: Symbol to trade
            lookback: Lookback period for high calculation
            position_size: Fraction of portfolio to use
        """
        super().__init__(name=f"Breakout_{lookback}")
        self.symbol = symbol
        self.lookback = lookback
        self.position_size = position_size

        # Track recent highs
        self.recent_highs = []

    def on_start(self):
        """Called when strategy starts."""
        print(f"Starting {self.name} for {self.symbol}")
        print(f"Lookback period: {self.lookback} days")

    def on_bar(self, bar: Bar):
        """Process each bar."""
        if bar.symbol != self.symbol:
            return

        # Track recent highs
        self.recent_highs.append(bar.high)

        # Need enough data
        if len(self.recent_highs) < self.lookback:
            return

        # Keep only what we need
        if len(self.recent_highs) > self.lookback:
            self.recent_highs = self.recent_highs[-self.lookback:]

        # Calculate highest high over lookback period (excluding today)
        highest_high = max(self.recent_highs[:-1])

        # Get current position
        position = self.context.get_position(self.symbol)
        has_position = position and position.quantity > 0

        # Entry: Price breaks above recent high
        if bar.close > highest_high and not has_position:
            available_cash = self.context.cash * self.position_size
            shares = int(available_cash / bar.close)

            if shares > 0:
                print(f"{bar.timestamp.date()}: BREAKOUT! Buy {shares} shares at ${bar.close:.2f}")
                print(f"  Price broke above ${highest_high:.2f}")
                self.context.buy(self.symbol, shares)

        # Exit: Simple trailing stop at 10% below entry
        elif has_position:
            stop_price = position.avg_entry_price * 0.90
            if bar.close <= stop_price:
                print(f"{bar.timestamp.date()}: STOP LOSS! Sell {position.quantity} shares at ${bar.close:.2f}")
                print(f"  Entry: ${position.avg_entry_price:.2f}, Loss: {position.unrealized_pnl_percent:.2f}%")
                self.context.sell(self.symbol, position.quantity)

    def on_stop(self):
        """Called when strategy stops."""
        print(f"\n{self.name} completed")


def test_eodhd_connection():
    """Test EODHD connection and show available features."""
    api_key = os.getenv("EODHD_API_KEY")

    if not api_key:
        print("ERROR: EODHD_API_KEY not found in .env file")
        print("Please add your EODHD API key to the .env file:")
        print("EODHD_API_KEY=your_api_key_here")
        return False

    print("Testing EODHD connection...")
    provider = EODHDProvider(api_key=api_key)

    # Test basic data fetch
    try:
        end = datetime.now()
        start = end - timedelta(days=7)
        bars = provider.get_bars("AAPL", start, end)

        if bars:
            print(f"✓ Successfully fetched {len(bars)} bars for AAPL")
            print(f"  Latest: {bars[-1].timestamp.date()} - Close: ${bars[-1].close:.2f}")
        else:
            print("✗ No data returned")
            return False

    except Exception as e:
        print(f"✗ Error fetching data: {e}")
        return False

    # Test extra features
    try:
        print("\nTesting EODHD extra features:")

        # Real-time price
        price = provider.get_real_time_price("AAPL")
        if price:
            print(f"✓ Real-time price for AAPL: ${price:.2f}")

        # Symbol search
        results = provider.search_symbol("Apple")
        if results:
            print(f"✓ Symbol search found {len(results)} results for 'Apple'")

    except Exception as e:
        print(f"Note: Some extra features may require higher API tier: {e}")

    print("\n" + "="*60)
    return True


if __name__ == "__main__":
    # First, test the connection
    if not test_eodhd_connection():
        print("\nPlease fix the EODHD connection before running backtest.")
        exit(1)

    # Set up backtest parameters
    symbol = "SPY"
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()

    print(f"\nRunning backtest on {symbol}")
    print("="*60)

    # Get API key from environment
    api_key = os.getenv("EODHD_API_KEY")

    # Create EODHD data provider
    data_provider = EODHDProvider(api_key=api_key)

    # Create strategy
    strategy = SimpleBreakoutStrategy(symbol=symbol, lookback=20)

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
    print(f"Backtesting {symbol} from {start_date.date()} to {end_date.date()}")
    print("="*60)

    analytics = engine.run(verbose=True)

    # Print detailed report
    print("\n" + analytics.generate_report())

    # Show some stats
    trades = engine.get_trades()
    if not trades.empty:
        print(f"\nExecuted {len(trades)} trades")
        print("\nFirst 5 trades:")
        print(trades.head().to_string())
