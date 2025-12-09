# Paperhands Quick Start Guide

Get up and running with your first backtest in 5 minutes.

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Setup API Keys

For best data quality, we recommend EODHD:

1. Sign up at https://eodhistoricaldata.com/register (free tier available)
2. Get your API key
3. Create a `.env` file in the project root:
   ```bash
   EODHD_API_KEY=your_api_key_here
   ```

Alternatively, use Yahoo Finance (free, no API key needed, but lower data quality).

## Your First Backtest

Create a file `my_strategy.py`:

```python
from datetime import datetime, timedelta
from src.strategy.base import Strategy
from src.core.types import Bar
from src.data.yahoo_provider import YahooDataProvider
from src.backtest.engine import BacktestEngine


class MyStrategy(Strategy):
    """Simple buy-and-hold strategy."""

    def __init__(self, symbol):
        super().__init__()
        self.symbol = symbol
        self.bought = False

    def on_start(self):
        print(f"Strategy started for {self.symbol}")

    def on_bar(self, bar: Bar):
        # Buy on first bar
        if not self.bought and bar.symbol == self.symbol:
            shares = int(self.context.cash / bar.close)
            self.context.buy(self.symbol, shares)
            self.bought = True
            print(f"Bought {shares} shares at ${bar.close:.2f}")


# Set up and run backtest
if __name__ == "__main__":
    # Create strategy
    strategy = MyStrategy("SPY")

    # Create data provider
    data_provider = YahooDataProvider()

    # Create backtest engine
    engine = BacktestEngine(
        strategy=strategy,
        data_provider=data_provider,
        symbols=["SPY"],
        start_date=datetime.now() - timedelta(days=365),
        end_date=datetime.now(),
        initial_cash=100000.0
    )

    # Run it!
    analytics = engine.run()

    # See results
    print(analytics.generate_report())
```

Run it:
```bash
python my_strategy.py
```

## Next Steps

### 1. Try the Examples

```bash
# Simple moving average strategy
python examples/simple_sma_strategy.py

# Advanced momentum strategy with risk management
python examples/advanced_strategy.py
```

### 2. Customize Parameters

```python
# Backtest with different settings
engine = BacktestEngine(
    strategy=strategy,
    data_provider=data_provider,
    symbols=["SPY"],
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2023, 12, 31),
    initial_cash=50000.0,
    commission_per_share=0.005,  # $0.005 per share
    slippage_percent=0.1,        # 0.1% slippage
    timeframe="1Hour"            # Hourly bars instead of daily
)
```

### 3. Add More Symbols

```python
# Trade multiple stocks
symbols = ["SPY", "QQQ", "IWM", "DIA"]

engine = BacktestEngine(
    strategy=strategy,
    data_provider=data_provider,
    symbols=symbols,  # Strategy will receive bars for all symbols
    # ... other params
)
```

### 4. Implement Your Trading Logic

Key methods in your strategy:

```python
class MyStrategy(Strategy):
    def on_start(self):
        # Initialize - load parameters, set up state
        pass

    def on_bar(self, bar: Bar):
        # Main logic - analyze bar and make trading decisions

        # Get current position
        position = self.context.get_position(bar.symbol)

        # Access portfolio info
        cash = self.context.cash
        portfolio_value = self.context.portfolio_value

        # Submit orders
        self.context.buy(bar.symbol, quantity=100)
        self.context.sell(bar.symbol, quantity=50)

        # Get historical data
        hist = self.context.get_historical_bars(
            bar.symbol,
            start=bar.timestamp - timedelta(days=30),
            end=bar.timestamp
        )

    def on_fill(self, fill_event):
        # React to fills - e.g., place stop loss orders
        pass

    def on_stop(self):
        # Cleanup - close positions, final logging
        pass
```

### 5. Analyze Results

```python
# After running backtest
analytics = engine.run()

# Get metrics
metrics = analytics.calculate_metrics()
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")

# Get equity curve
equity_curve = engine.get_equity_curve()
print(equity_curve.head())

# Get trade history
trades = engine.get_trades()
print(trades)

# Full report
print(analytics.generate_report())
```

## Using Different Data Providers

### EODHD (Recommended)

```python
import os
from dotenv import load_dotenv
from src.data.eodhd_provider import EODHDProvider

load_dotenv()
data_provider = EODHDProvider(api_key=os.getenv("EODHD_API_KEY"))

# Use in engine as normal
engine = BacktestEngine(
    strategy=strategy,
    data_provider=data_provider,
    # ... rest of params
)
```

### Alpaca

```python
from src.data.alpaca_provider import AlpacaDataProvider

data_provider = AlpacaDataProvider(
    api_key="YOUR_API_KEY",
    secret_key="YOUR_SECRET_KEY",
    paper=True
)
```

Get Alpaca keys:
1. Sign up at https://alpaca.markets (free)
2. Go to Paper Trading dashboard
3. Generate API keys

### Yahoo Finance (Free, No API Key)

```python
from src.data.yahoo_provider import YahooDataProvider

data_provider = YahooDataProvider()  # No API key needed
```

## Common Patterns

### Position Sizing

```python
# Risk-based sizing
shares = self.context.calculate_position_size(
    symbol="SPY",
    price=450.0,
    risk_percent=2.0  # Risk 2% of portfolio
)

# Fixed dollar amount
shares = self.context.calculate_position_size_fixed_amount(
    price=450.0,
    amount=10000  # Invest $10,000
)

# Manual sizing
available_cash = self.context.cash * 0.9  # Use 90% of cash
shares = int(available_cash / price)

# Check if affordable
if self.context.can_afford(symbol, shares, price):
    self.context.buy(symbol, shares)
```

### Stop Losses

```python
def on_bar(self, bar: Bar):
    position = self.context.get_position(bar.symbol)

    if position:
        # Check if price fell below stop loss
        stop_price = position.avg_entry_price * 0.95  # 5% stop
        if bar.close <= stop_price:
            self.context.sell(bar.symbol, position.quantity)
```

### Technical Indicators

```python
def calculate_sma(self, prices, window):
    """Simple moving average."""
    if len(prices) < window:
        return None
    return sum(prices[-window:]) / window

def calculate_rsi(self, prices, period=14):
    """Relative Strength Index."""
    if len(prices) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
```

## Need Help?

- Check `README.md` for full documentation
- Look at example strategies in `examples/`
- Review source code - it's well-commented!

## Ready to Go Live?

Once your backtest looks good:

1. The same strategy code will work for live trading
2. Just swap `BacktestBroker` for `AlpacaBroker` (to be implemented)
3. Your strategy never knows the difference!

This is the key advantage of the framework - **write once, backtest and trade with the same code**.
