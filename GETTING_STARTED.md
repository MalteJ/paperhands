# Getting Started with Paperhands

Welcome! This guide will get you from zero to running your first backtest in minutes.

## What You Have

A complete backtesting framework for stock trading strategies with:
- ✅ **EODHD integration** (high-quality data)
- ✅ **Portable strategies** (same code for backtest & live trading)
- ✅ **Full analytics** (Sharpe ratio, drawdown, win rate, etc.)
- ✅ **Position sizing** and risk management
- ✅ **Multiple data providers** (EODHD, Yahoo, Alpaca)

## Quick Start (3 Steps)

### 1. Install Dependencies

```bash
# Make sure your virtual environment is activated
pip install -r requirements.txt
```

### 2. Set Up Your API Key

Your EODHD API key is already in `.env` - you're all set! ✓

To verify:
```bash
python validate_setup.py
```

### 3. Run Your First Backtest

```bash
python examples/eodhd_strategy.py
```

That's it! You should see a backtest running on SPY with full performance metrics.

## What Just Happened?

The example strategy:
1. Loaded 1 year of SPY data from EODHD
2. Applied a breakout trading strategy
3. Simulated realistic order execution
4. Calculated comprehensive performance metrics

## Next Steps

### Try Other Examples

```bash
# Simple moving average crossover (Yahoo data - free)
python examples/simple_sma_strategy.py

# Advanced momentum strategy with risk management
python examples/advanced_strategy.py
```

### Build Your Own Strategy

Create a new file `my_strategy.py`:

```python
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.strategy.base import Strategy
from src.core.types import Bar
from src.data.eodhd_provider import EODHDProvider
from src.backtest.engine import BacktestEngine

load_dotenv()


class MyStrategy(Strategy):
    """Your custom strategy here."""

    def on_start(self):
        print("Strategy starting...")

    def on_bar(self, bar: Bar):
        # Your trading logic here
        # Example: Buy on first bar
        if not self.context.has_position(bar.symbol):
            shares = int(self.context.cash * 0.95 / bar.close)
            if shares > 0:
                self.context.buy(bar.symbol, shares)


# Run backtest
if __name__ == "__main__":
    provider = EODHDProvider(api_key=os.getenv("EODHD_API_KEY"))
    strategy = MyStrategy()

    engine = BacktestEngine(
        strategy=strategy,
        data_provider=provider,
        symbols=["AAPL"],
        start_date=datetime.now() - timedelta(days=365),
        end_date=datetime.now(),
        initial_cash=100000.0
    )

    analytics = engine.run()
    print(analytics.generate_report())
```

Run it:
```bash
python my_strategy.py
```

## Learning Resources

### Documentation
- **QUICKSTART.md** - 5-minute intro with examples
- **README.md** - Complete framework documentation
- **DATA_PROVIDERS.md** - All about data sources
- **INSTALL.md** - Detailed installation guide

### Examples (in `examples/` directory)
- `simple_sma_strategy.py` - Moving average crossover
- `advanced_strategy.py` - Momentum with risk management
- `eodhd_strategy.py` - Using EODHD provider

### Code Structure
```
src/
├── core/        - Bar, Order, Position types
├── data/        - Data providers (EODHD, Yahoo, Alpaca)
├── strategy/    - Strategy base class and context
├── execution/   - Order execution (backtest & live)
├── portfolio/   - Portfolio and P&L tracking
└── backtest/    - Backtesting engine and analytics
```

## Common Tasks

### Add a New Symbol

```python
symbols = ["AAPL", "MSFT", "GOOGL"]  # Instead of just one

engine = BacktestEngine(
    strategy=strategy,
    data_provider=provider,
    symbols=symbols,  # Multiple symbols
    # ... other params
)
```

### Use Hourly Data

```python
engine = BacktestEngine(
    # ... other params
    timeframe="1Hour"  # Instead of "1Day"
)
```

### Add Position Sizing

```python
def on_bar(self, bar: Bar):
    # Risk 2% of portfolio per trade
    shares = self.context.calculate_position_size(
        bar.symbol,
        bar.close,
        risk_percent=2.0
    )

    if shares > 0 and self.context.can_afford(bar.symbol, shares, bar.close):
        self.context.buy(bar.symbol, shares)
```

### Add Stop Loss

```python
def on_bar(self, bar: Bar):
    position = self.context.get_position(bar.symbol)

    if position:
        # 5% stop loss
        stop_price = position.avg_entry_price * 0.95
        if bar.close <= stop_price:
            self.context.sell(bar.symbol, position.quantity)
```

## Tips for Success

1. **Start Simple**: Get a basic strategy working first
2. **Test with Yahoo**: Use free Yahoo data while learning
3. **Use EODHD for Real Work**: Higher quality data matters
4. **Cache Your Data**: Avoid repeated API calls (see DATA_PROVIDERS.md)
5. **Check the Examples**: Learn from working code
6. **Read the Docstrings**: The code is well-documented

## Troubleshooting

### No data returned
- Check your API key in `.env`
- Verify the symbol exists (e.g., "AAPL" not "Apple")
- Try a different date range

### Import errors
- Make sure venv is activated
- Run `pip install -r requirements.txt`
- Check you're in the project root directory

### Rate limit errors
- EODHD free tier: 20 calls/day
- Implement caching (see DATA_PROVIDERS.md)
- Consider upgrading to paid tier

### Strategy not trading
- Add print statements in `on_bar()`
- Check if conditions are being met
- Verify you have enough cash: `print(self.context.cash)`

## Your EODHD Free Tier

You have **20 API calls per day** with the free tier. This is enough for:
- Testing strategies on 1-2 symbols
- Learning the framework
- Developing your strategy logic

**Tips to maximize free tier:**
1. Cache downloaded data locally
2. Test with shorter time periods initially
3. Use Yahoo Finance while developing
4. Upgrade when ready for serious backtesting ($79.99/month for 100K calls/day)

## Ready to Go Live?

When your strategy is profitable in backtesting:

1. Set up Alpaca paper trading (free)
2. The same strategy code will work - just swap the broker
3. Test in paper trading first
4. Go live when confident

The key advantage: **write once, backtest and trade with the same code**.

## Need Help?

- Check the documentation files (README, QUICKSTART, etc.)
- Look at the examples
- Read the source code docstrings
- Run `python validate_setup.py` to check your setup

## What's Next?

1. ✅ You've installed everything
2. ✅ Your EODHD API key is configured
3. ⬜ Run the examples
4. ⬜ Build your first strategy
5. ⬜ Add risk management
6. ⬜ Optimize parameters
7. ⬜ Prepare for live trading

**Happy backtesting! 🚀**
