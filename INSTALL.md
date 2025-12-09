# Installation Guide

Complete setup instructions for Paperhands.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Step-by-Step Installation

### 1. Clone/Download the Project

If you haven't already, navigate to the project directory:

```bash
cd paperhands
```

### 2. Create Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- pandas, numpy (data handling)
- tqdm (progress bars)
- requests (HTTP for EODHD API)
- python-dotenv (environment variables)
- yfinance (Yahoo Finance data - optional)
- alpaca-py (Alpaca API - optional)

### 4. Set Up API Keys

#### Option A: EODHD (Recommended for Quality Data)

1. Sign up at https://eodhistoricaldata.com/register
2. Get your API key from the dashboard
3. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` and add your key:
   ```
   EODHD_API_KEY=your_actual_key_here
   ```

**EODHD Features:**
- High-quality historical data
- Good US stock coverage
- Fundamental data
- Options data (for future use)
- Free tier: 20 API calls/day, historical EOD data
- Paid tiers: More calls, intraday data, real-time

#### Option B: Yahoo Finance (Free, No API Key)

No setup needed! Just use `YahooDataProvider()` in your code.

**Pros:**
- Completely free
- No API key needed
- Good for learning

**Cons:**
- Data quality varies
- No official API (uses web scraping)
- May be rate-limited
- Could break if Yahoo changes their site

#### Option C: Alpaca (For Live Trading Later)

1. Sign up at https://alpaca.markets
2. Go to Paper Trading dashboard
3. Generate API keys
4. Add to `.env`:
   ```
   ALPACA_API_KEY=your_key
   ALPACA_SECRET_KEY=your_secret
   ```

### 5. Validate Installation

Run the validation script:

```bash
python validate_setup.py
```

This checks:
- Python version
- Required packages
- .env file
- API connections
- Core framework

### 6. Run Your First Backtest

Try one of the examples:

```bash
# Using Yahoo Finance (no API key needed)
python examples/simple_sma_strategy.py

# Using EODHD (requires API key in .env)
python examples/eodhd_strategy.py

# Advanced multi-stock strategy
python examples/advanced_strategy.py
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`, make sure:
1. Virtual environment is activated
2. You ran `pip install -r requirements.txt`
3. You're in the project root directory

### EODHD API Errors

**401 Unauthorized:**
- Check your API key is correct in `.env`
- Make sure you copied the full key (no spaces)

**429 Rate Limit:**
- Free tier has 20 calls/day limit
- Wait until next day or upgrade plan

**404 Symbol Not Found:**
- Check symbol format (e.g., "AAPL" for US stocks)
- EODHD uses format: SYMBOL.EXCHANGE (handled automatically)

### Yahoo Finance Errors

**No data returned:**
- Yahoo may be temporarily unavailable
- Try a different symbol
- Check your internet connection

**SSL Certificate errors:**
- Update certifi: `pip install --upgrade certifi`

### Windows-Specific Issues

**"python not found":**
- Use `py` instead of `python`
- Or add Python to PATH

**Virtual environment activation:**
- Use `venv\Scripts\activate` (not `source`)
- Or use PowerShell: `venv\Scripts\Activate.ps1`

### macOS/Linux Issues

**Permission denied:**
- Use `python3` instead of `python`
- Make sure scripts are executable: `chmod +x script.py`

## Optional: Development Setup

If you want to contribute or modify the framework:

```bash
# Install development dependencies
pip install pytest black flake8 mypy

# Run tests
pytest

# Format code
black src/

# Lint code
flake8 src/
```

## Upgrading

To update dependencies:

```bash
pip install --upgrade -r requirements.txt
```

## Uninstalling

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment directory
rm -rf venv  # macOS/Linux
rmdir /s venv  # Windows

# That's it - all dependencies were in the venv
```

## Next Steps

1. Read `QUICKSTART.md` for a 5-minute intro
2. Check out examples in `examples/` directory
3. Read `README.md` for full documentation
4. Start building your own strategies!

## Getting Help

- Check examples in `examples/` directory
- Read docstrings in source code
- Check GitHub issues (if applicable)
- Make sure `.env` file has correct API keys

## Recommended Learning Path

1. **Start Simple**: Run `simple_sma_strategy.py` with Yahoo data
2. **Add Quality Data**: Get EODHD API key, run `eodhd_strategy.py`
3. **Learn Patterns**: Study `advanced_strategy.py` for risk management
4. **Build Your Own**: Create custom strategies using examples as templates
5. **Prepare for Live**: When ready, set up Alpaca for live trading
