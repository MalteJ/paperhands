"""
Setup Validation Script

Run this script to validate your environment and data providers are working.
"""

import sys
import os
from pathlib import Path

# Add current directory to path so we can import src
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Paperhands Setup Validation")
print("=" * 60)

# Check Python version
print(f"\n1. Python Version: {sys.version}")
if sys.version_info < (3, 9):
    print("   [!] Warning: Python 3.9+ recommended")
else:
    print("   [OK] Python version OK")

# Check required packages
print("\n2. Checking required packages...")
required_packages = [
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("tqdm", "tqdm"),
    ("requests", "requests"),
    ("dotenv", "python-dotenv"),
]

missing_packages = []
for module_name, package_name in required_packages:
    try:
        __import__(module_name)
        print(f"   ✓ {package_name} installed")
    except ImportError:
        print(f"   ✗ {package_name} NOT installed")
        missing_packages.append(package_name)

if missing_packages:
    print(f"\n   Missing packages: {', '.join(missing_packages)}")
    print("   Install with: pip install -r requirements.txt")
    sys.exit(1)

# Check .env file
print("\n3. Checking .env file...")
if os.path.exists(".env"):
    print("   ✓ .env file exists")

    from dotenv import load_dotenv
    load_dotenv()

    # Check EODHD API key
    eodhd_key = os.getenv("EODHD_API_KEY")
    if eodhd_key:
        print(f"   ✓ EODHD_API_KEY found (length: {len(eodhd_key)})")
    else:
        print("   ⚠ EODHD_API_KEY not found in .env")
        print("     Add it if you want to use EODHD provider")

    # Check Alpaca keys
    alpaca_key = os.getenv("ALPACA_API_KEY")
    if alpaca_key:
        print(f"   ✓ ALPACA_API_KEY found")
    else:
        print("   ⚠ ALPACA_API_KEY not found (optional)")

else:
    print("   ⚠ .env file not found")
    print("     Create one based on .env.example if using EODHD or Alpaca")

# Test data providers
print("\n4. Testing data providers...")

# Test Yahoo (free, no API key needed)
try:
    from src.data.yahoo_provider import YahooDataProvider
    print("   ✓ Yahoo provider imported successfully")

    print("     Testing Yahoo data fetch...")
    from datetime import datetime, timedelta

    provider = YahooDataProvider()
    end = datetime.now()
    start = end - timedelta(days=7)

    bars = provider.get_bars("SPY", start, end, "1Day")
    if bars:
        print(f"     ✓ Yahoo: Fetched {len(bars)} bars for SPY")
        print(f"       Latest: {bars[-1].timestamp.date()} - Close: ${bars[-1].close:.2f}")
    else:
        print("     ⚠ Yahoo: No data returned")

except Exception as e:
    print(f"   ✗ Yahoo provider error: {e}")

# Test EODHD if API key exists
if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()
    eodhd_key = os.getenv("EODHD_API_KEY")

    if eodhd_key:
        try:
            from src.data.eodhd_provider import EODHDProvider
            print("   ✓ EODHD provider imported successfully")

            print("     Testing EODHD data fetch...")
            provider = EODHDProvider(api_key=eodhd_key)

            bars = provider.get_bars("AAPL", start, end, "1Day")
            if bars:
                print(f"     ✓ EODHD: Fetched {len(bars)} bars for AAPL")
                print(f"       Latest: {bars[-1].timestamp.date()} - Close: ${bars[-1].close:.2f}")
            else:
                print("     ⚠ EODHD: No data returned")

        except Exception as e:
            print(f"   ✗ EODHD provider error: {e}")
            print(f"     Check your API key is valid")

# Test core framework
print("\n5. Testing core framework...")
try:
    from src.core.types import Bar, Order, Position, OrderType, OrderSide
    from src.strategy.base import Strategy
    from src.backtest.engine import BacktestEngine
    from src.portfolio.portfolio import Portfolio

    print("   ✓ All core modules imported successfully")

    # Quick test
    portfolio = Portfolio(initial_cash=100000.0)
    assert portfolio.cash == 100000.0
    print("   ✓ Portfolio test passed")

except Exception as e:
    print(f"   ✗ Core framework error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("VALIDATION COMPLETE")
print("=" * 60)

if missing_packages:
    print("\n⚠ Some packages are missing. Install them first.")
elif not os.path.exists(".env"):
    print("\n✓ Core framework is working!")
    print("⚠ Create a .env file if you want to use EODHD or Alpaca")
    print("\nNext steps:")
    print("  1. Copy .env.example to .env")
    print("  2. Add your API keys")
    print("  3. Run: python examples/eodhd_strategy.py")
else:
    print("\n✓ Everything looks good!")
    print("\nNext steps:")
    print("  - Run: python examples/simple_sma_strategy.py")
    print("  - Run: python examples/eodhd_strategy.py")
    print("  - Check out the examples/ directory for more")
    print("\nHappy trading!")
