# Paperhands - Trading Strategy Backtesting Framework

A Python framework for developing and backtesting stock and options trading strategies with seamless portability between backtesting and live trading.

## Features

- **Portable Strategy Code**: Write strategies once, use them in both backtesting and live trading
- **Event-Driven Architecture**: Realistic simulation of live trading conditions
- **Pluggable Data Providers**: Support for Alpaca, Yahoo Finance, or custom data sources
- **Comprehensive Analytics**: Sharpe ratio, max drawdown, win rate, and more
- **Position Sizing**: Built-in risk management and position sizing helpers
- **Multiple Timeframes**: Support for hourly, daily, and custom timeframes
- **Commission & Slippage**: Realistic simulation of trading costs

## Installation

```bash
# Clone or download the repository
cd paperhands

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Simple Moving Average Strategy

```python
from datetime import datetime, timedelta
from src.strategy.base import Strategy
from src.core.types import Bar
from src.data.yahoo_provider import YahooDataProvider
from src.backtest.engine import BacktestEngine


class SMAStrategy(Strategy):
    def __init__(self, symbol, short_window=20, long_window=50):
        super().__init__()
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        self.closes = []

    def on_start(self):
        print(f"Starting strategy for {self.symbol}")

    def on_bar(self, bar: Bar):
        if bar.symbol != self.symbol:
            return

        self.closes.append(bar.close)

        if len(self.closes) < self.long_window:
            return

        # Calculate SMAs
        short_sma = sum(self.closes[-self.short_window:]) / self.short_window
        long_sma = sum(self.closes[-self.long_window:]) / self.long_window

        position = self.context.get_position(self.symbol)
        current_position = position.quantity if position else 0

        # Buy when short SMA crosses above long SMA
        if short_sma > long_sma and current_position == 0:
            shares = int(self.context.cash * 0.95 / bar.close)
            if shares > 0:
                self.context.buy(self.symbol, shares)

        # Sell when short SMA crosses below long SMA
        elif short_sma < long_sma and current_position > 0:
            self.context.sell(self.symbol, current_position)


# Run backtest
data_provider = YahooDataProvider()
strategy = SMAStrategy("SPY", short_window=20, long_window=50)

engine = BacktestEngine(
    strategy=strategy,
    data_provider=data_provider,
    symbols=["SPY"],
    start_date=datetime.now() - timedelta(days=365),
    end_date=datetime.now(),
    initial_cash=100000.0
)

analytics = engine.run()
print(analytics.generate_report())
```

### 2. Using EODHD Data Provider (Recommended)

```python
import os
from dotenv import load_dotenv
from src.data.eodhd_provider import EODHDProvider

# Load API key from .env file
load_dotenv()

# Initialize with your EODHD API key
data_provider = EODHDProvider(
    api_key=os.getenv("EODHD_API_KEY")
)

# Use in backtesting engine as shown above
```

### 3. Using Alpaca Data Provider

```python
from src.data.alpaca_provider import AlpacaDataProvider

# Initialize with your Alpaca credentials
data_provider = AlpacaDataProvider(
    api_key="YOUR_API_KEY",
    secret_key="YOUR_SECRET_KEY",
    paper=True  # Use paper trading
)

# Use in backtesting engine as shown above
```

## Project Structure

```
paperhands/
├── src/
│   ├── core/           # Core types (Bar, Order, Position, etc.)
│   ├── data/           # Data provider interfaces and implementations
│   ├── strategy/       # Strategy base classes and context
│   ├── execution/      # Broker interfaces (backtest and live)
│   ├── portfolio/      # Portfolio and position management
│   └── backtest/       # Backtesting engine and analytics
├── examples/           # Example strategies
├── tests/             # Unit tests
└── requirements.txt   # Python dependencies
```

## Key Concepts

### Strategy

Inherit from `Strategy` and implement:
- `on_start()`: Initialization logic
- `on_bar(bar)`: Called for each new price bar - main trading logic here
- `on_fill(fill_event)`: Optional, called when orders are filled
- `on_stop()`: Cleanup logic

### Context

The `context` object provides access to:
- **Portfolio**: `context.cash`, `context.portfolio_value`, `context.get_position(symbol)`
- **Orders**: `context.buy()`, `context.sell()`, `context.submit_order()`
- **Data**: `context.get_historical_bars()`, `context.get_latest_bar()`
- **Position Sizing**: `context.calculate_position_size()`, `context.can_afford()`

### Data Providers

Implement the `DataProvider` interface:
- `get_bars()`: Get historical bars
- `get_bars_df()`: Get historical data as DataFrame
- `get_latest_bar()`: Get most recent bar

Built-in providers:
- `EODHDProvider`: EODHD historical data (recommended - high quality, good US coverage)
- `YahooDataProvider`: Free data via yfinance (free but may have quality issues)
- `AlpacaDataProvider`: Alpaca historical data

### Backtesting

The `BacktestEngine` orchestrates the backtest:
1. Loads historical data
2. Iterates through each bar chronologically
3. Calls strategy's `on_bar()` for each bar
4. Simulates order execution with realistic fill logic
5. Tracks portfolio state and performance

## Performance Metrics

The framework calculates:
- Total return ($ and %)
- Sharpe ratio
- Sortino ratio
- Maximum drawdown
- Maximum drawdown duration
- Win rate
- Profit factor
- Average trade P&L
- Largest win/loss

## Moving to Live Trading

The key advantage of this framework is portability. Your strategy code remains unchanged when moving from backtest to live trading.

**Backtest** uses:
- `BacktestBroker`: Simulates order execution
- Historical `DataProvider`: Provides past data

**Live Trading** would use:
- `AlpacaBroker`: Submits real orders to Alpaca (to be implemented)
- Live `DataProvider`: Provides real-time data

The strategy only interacts with the `StrategyContext`, so the same code works in both environments.

## Examples

See the `examples/` directory for:
- `simple_sma_strategy.py`: Basic moving average crossover
- `advanced_strategy.py`: Momentum strategy with risk management

Run examples:
```bash
python examples/simple_sma_strategy.py
python examples/advanced_strategy.py
python examples/eodhd_strategy.py  # Using EODHD data
```

## Configuration

### EODHD Setup (Recommended)

1. Sign up for EODHD account at https://eodhistoricaldata.com/register
2. Get your API key from the dashboard
3. Create a `.env` file in the project root (see `.env.example`):
   ```bash
   EODHD_API_KEY=your_api_key_here
   ```
4. Use in your code:
   ```python
   import os
   from dotenv import load_dotenv
   from src.data.eodhd_provider import EODHDProvider

   load_dotenv()
   data_provider = EODHDProvider(api_key=os.getenv("EODHD_API_KEY"))
   ```

EODHD offers:
- High-quality historical data
- Good US market coverage
- Fundamental data access
- Options data (for future features)
- Free tier available for testing

### Alpaca Setup

1. Sign up for Alpaca account (free paper trading)
2. Get API keys from dashboard
3. Set environment variables or pass to `AlpacaDataProvider`:
   ```python
   import os

   data_provider = AlpacaDataProvider(
       api_key=os.getenv("ALPACA_API_KEY"),
       secret_key=os.getenv("ALPACA_SECRET_KEY"),
       paper=True
   )
   ```

### Timeframes

Supported timeframes:
- `"1Min"`: 1-minute bars
- `"5Min"`: 5-minute bars
- `"15Min"`: 15-minute bars
- `"1Hour"`: Hourly bars
- `"1Day"`: Daily bars (end-of-day)

## Risk Management

Built-in helpers for position sizing:
```python
# Risk-based sizing (risk X% of portfolio)
shares = context.calculate_position_size(symbol, price, risk_percent=2.0)

# Fixed dollar amount
shares = context.calculate_position_size_fixed_amount(price, amount=10000)

# Check affordability
if context.can_afford(symbol, shares, price):
    context.buy(symbol, shares)
```

## Roadmap

- [ ] Live trading implementation (Alpaca broker)
- [ ] Options support (chains, Greeks, strategies)
- [ ] More data providers (Polygon, IEX)
- [ ] Vectorized backtesting mode
- [ ] Parameter optimization
- [ ] Walk-forward analysis
- [ ] Paper trading mode
- [ ] Web dashboard for monitoring

## Contributing

Contributions welcome! This is a framework designed for extensibility.

## License

MIT License - feel free to use for personal or commercial projects.

## Disclaimer

This software is for educational purposes. Always test strategies thoroughly before risking real capital. Past performance does not guarantee future results.
