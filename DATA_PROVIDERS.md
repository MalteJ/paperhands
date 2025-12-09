# Data Provider Guide

Comprehensive guide to using different data providers in Paperhands.

## Overview

The framework uses a pluggable data provider architecture. All providers implement the same `DataProvider` interface, so switching between them is easy.

## Quick Comparison

| Provider | Cost | Data Quality | Setup | Best For |
|----------|------|--------------|-------|----------|
| **EODHD** | Free tier + Paid | High | API key | Production backtesting |
| **Yahoo Finance** | Free | Variable | None | Learning, testing |
| **Alpaca** | Free | High | API key | Live trading integration |

## EODHD (Recommended)

### Why EODHD?

- **High-quality data**: Professional-grade historical data
- **Good coverage**: Comprehensive US stock data
- **Extras**: Fundamental data, options data, real-time prices
- **Reliable**: Stable API with good uptime
- **Affordable**: Free tier for learning, reasonable paid tiers

### Setup

1. **Sign up**: https://eodhistoricaldata.com/register
2. **Get API key**: Dashboard → API Keys
3. **Add to .env**:
   ```
   EODHD_API_KEY=your_key_here
   ```

### Pricing Tiers

**All Access APIs - $79.99/month (Recommended for serious backtesting):**
- 100,000 API calls/day
- All historical EOD data
- Intraday data (1-minute intervals)
- Fundamental data
- Real-time data
- Options data

**Free Tier (Good for learning):**
- 20 API calls/day
- Historical EOD data only
- Good for testing the framework

### Usage Examples

#### Basic Usage

```python
import os
from dotenv import load_dotenv
from src.data.eodhd_provider import EODHDProvider

# Load environment variables
load_dotenv()

# Initialize provider
provider = EODHDProvider(api_key=os.getenv("EODHD_API_KEY"))

# Get historical data
from datetime import datetime, timedelta

end = datetime.now()
start = end - timedelta(days=365)

# Get bars
bars = provider.get_bars("AAPL", start, end, timeframe="1Day")
print(f"Got {len(bars)} bars")

# Get as DataFrame
df = provider.get_bars_df("AAPL", start, end, timeframe="1Day")
print(df.head())

# Get multiple symbols
symbols = ["AAPL", "MSFT", "GOOGL"]
data = provider.get_bars_multi(symbols, start, end)
```

#### Advanced Features

EODHD provides extra features beyond the base DataProvider interface:

```python
# Get fundamental data
fundamentals = provider.get_fundamentals("AAPL")
print(fundamentals["General"]["Name"])
print(fundamentals["Highlights"]["MarketCapitalization"])

# Get real-time price
price = provider.get_real_time_price("AAPL")
print(f"Current price: ${price:.2f}")

# Search for symbols
results = provider.search_symbol("Apple")
for result in results[:5]:
    print(f"{result['Code']} - {result['Name']}")
```

#### Custom Exchange

```python
# For non-US stocks, specify exchange
provider = EODHDProvider(
    api_key=os.getenv("EODHD_API_KEY"),
    exchange="LSE"  # London Stock Exchange
)

bars = provider.get_bars("BP", start, end)  # BP on LSE
```

### Rate Limiting

EODHD has built-in rate limiting (100ms between requests). For faster backtests:

```python
provider = EODHDProvider(api_key=api_key)
provider.rate_limit_delay = 0.05  # 50ms (be careful not to exceed limits)
```

### Best Practices

1. **Cache data**: Save historical data locally to avoid repeated API calls
2. **Batch requests**: Use `get_bars_multi()` for multiple symbols
3. **Monitor usage**: Check your dashboard for API call usage
4. **Start with free tier**: Test your strategy before upgrading

## Yahoo Finance

### Why Yahoo Finance?

- **Free**: No cost, no API key
- **Easy**: Zero setup
- **Good for learning**: Perfect for getting started

### Limitations

- Data quality can vary
- No official API (uses web scraping)
- May be rate-limited
- Could break if Yahoo changes their site
- Limited historical data in some cases

### Usage

```python
from src.data.yahoo_provider import YahooDataProvider

# No API key needed
provider = YahooDataProvider()

# Same interface as other providers
bars = provider.get_bars("SPY", start, end, timeframe="1Day")
df = provider.get_bars_df("SPY", start, end, timeframe="1Day")
```

### Supported Timeframes

- `"1Day"`: Daily bars
- `"1Hour"`: Hourly bars
- `"30Min"`: 30-minute bars
- `"15Min"`: 15-minute bars
- `"5Min"`: 5-minute bars
- `"1Min"`: 1-minute bars (recent data only)

### Best Practices

1. **Add error handling**: Yahoo can be unreliable
2. **Use for learning**: Great for testing strategies
3. **Cache data**: Save downloaded data locally
4. **Verify data**: Check for missing or incorrect bars

## Alpaca

### Why Alpaca?

- **Live trading**: Same API for backtesting and live trading
- **Free paper trading**: Test with real-time data
- **Commission-free**: No trading fees
- **Good data quality**: Professional-grade data

### Setup

1. **Sign up**: https://alpaca.markets
2. **Get API keys**: Dashboard → Paper Trading → Generate
3. **Add to .env**:
   ```
   ALPACA_API_KEY=your_key
   ALPACA_SECRET_KEY=your_secret
   ```

### Usage

```python
import os
from src.data.alpaca_provider import AlpacaDataProvider

provider = AlpacaDataProvider(
    api_key=os.getenv("ALPACA_API_KEY"),
    secret_key=os.getenv("ALPACA_SECRET_KEY"),
    paper=True  # Use paper trading
)

# Same interface
bars = provider.get_bars("AAPL", start, end, timeframe="1Day")
```

### Supported Timeframes

- `"1Min"`: 1-minute bars
- `"5Min"`: 5-minute bars
- `"15Min"`: 15-minute bars
- `"1Hour"`: Hourly bars
- `"1Day"`: Daily bars

### Best For

- Strategies you plan to run live
- Paper trading practice
- Real-time data testing

## Creating Custom Providers

You can create your own data provider by implementing the `DataProvider` interface:

```python
from src.data.provider import DataProvider
from src.core.types import Bar
from datetime import datetime
from typing import List
import pandas as pd

class MyCustomProvider(DataProvider):
    def __init__(self, connection_string):
        self.connection = connection_string
        # Your initialization code

    def get_bars(self, symbol: str, start: datetime,
                 end: datetime, timeframe: str = "1Day") -> List[Bar]:
        # Fetch data from your source
        # Convert to Bar objects
        # Return sorted list
        pass

    def get_bars_df(self, symbol: str, start: datetime,
                    end: datetime, timeframe: str = "1Day") -> pd.DataFrame:
        # Return as DataFrame
        pass

    def get_latest_bar(self, symbol: str) -> Bar:
        # Get most recent bar
        pass
```

## Data Caching Strategy

To minimize API calls and speed up backtesting:

```python
import pickle
import os
from pathlib import Path

class CachedDataProvider:
    def __init__(self, provider, cache_dir="data/cache"):
        self.provider = provider
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_bars_cached(self, symbol, start, end, timeframe="1Day"):
        # Create cache key
        cache_key = f"{symbol}_{start.date()}_{end.date()}_{timeframe}.pkl"
        cache_path = self.cache_dir / cache_key

        # Check cache
        if cache_path.exists():
            print(f"Loading {symbol} from cache...")
            with open(cache_path, 'rb') as f:
                return pickle.load(f)

        # Fetch from provider
        print(f"Fetching {symbol} from API...")
        bars = self.provider.get_bars(symbol, start, end, timeframe)

        # Save to cache
        with open(cache_path, 'wb') as f:
            pickle.dump(bars, f)

        return bars

# Usage
from src.data.eodhd_provider import EODHDProvider
import os
from dotenv import load_dotenv

load_dotenv()
base_provider = EODHDProvider(api_key=os.getenv("EODHD_API_KEY"))
cached_provider = CachedDataProvider(base_provider)

# First call: fetches from API and caches
bars = cached_provider.get_bars_cached("AAPL", start, end)

# Second call: loads from cache (fast!)
bars = cached_provider.get_bars_cached("AAPL", start, end)
```

## Recommendation by Use Case

### Learning the Framework
→ **Yahoo Finance**: Free, no setup

### Serious Backtesting
→ **EODHD**: High quality data, affordable

### Preparing for Live Trading
→ **Alpaca**: Same API for backtest and live

### High-Frequency/Intraday Strategies
→ **EODHD** (paid tier) or **Alpaca**: Good intraday data

### Multiple Asset Classes (future)
→ **EODHD**: Has options, forex, crypto support

## Troubleshooting

### "Invalid API key"
- Check `.env` file has correct key
- No extra spaces or quotes
- Key is active in provider dashboard

### "Rate limit exceeded"
- You've hit your daily/hourly limit
- Implement caching
- Upgrade to higher tier
- Use fewer API calls (batch requests)

### "No data returned"
- Symbol might not exist
- Date range might be invalid
- Market was closed (check for holidays)
- Try a different symbol to verify connection

### Slow backtests
- Implement caching (see above)
- Use batch requests (`get_bars_multi()`)
- Reduce rate limiting delay (carefully)
- Consider downloading all data upfront

## Summary

- **Start with Yahoo** for learning (free, easy)
- **Upgrade to EODHD** for serious work (quality data)
- **Use Alpaca** when preparing for live trading (consistency)
- **Cache everything** to minimize API calls
- **Monitor your usage** to avoid hitting limits
