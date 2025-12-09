"""
Advanced Strategy Example with Position Sizing and Risk Management

This demonstrates more advanced features:
- Multiple symbols
- Position sizing based on portfolio risk
- Stop losses
- Take profits
- Using context helper methods
"""

from datetime import datetime, timedelta
from typing import Dict
from paperhands import Strategy, Bar, OrderType, FillEvent, YahooDataProvider, CachedDataProvider, BacktestEngine


class MomentumStrategy(Strategy):
    """
    Momentum strategy with risk management.

    Buys stocks showing strong momentum and uses stop losses and take profits.
    """

    def __init__(self, symbols: list, lookback: int = 20, risk_per_trade: float = 2.0,
                 stop_loss_pct: float = 5.0, take_profit_pct: float = 15.0):
        """
        Initialize strategy.

        Args:
            symbols: List of symbols to trade
            lookback: Lookback period for momentum calculation
            risk_per_trade: Percentage of portfolio to risk per trade
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
        """
        super().__init__(name="MomentumStrategy")
        self.symbols = symbols
        self.lookback = lookback
        self.risk_per_trade = risk_per_trade
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

        # Track price history
        self.price_history: Dict[str, list] = {symbol: [] for symbol in symbols}

        # Track entry prices for stop loss/take profit
        self.entry_prices: Dict[str, float] = {}

    def on_start(self):
        """Called when strategy starts."""
        print(f"Starting {self.name}")
        print(f"Trading: {', '.join(self.symbols)}")
        print(f"Lookback: {self.lookback} days")
        print(f"Risk per trade: {self.risk_per_trade}%")
        print(f"Stop loss: {self.stop_loss_pct}%, Take profit: {self.take_profit_pct}%")

    def calculate_momentum(self, symbol: str) -> float:
        """Calculate momentum as percentage change over lookback period."""
        prices = self.price_history[symbol]
        if len(prices) < self.lookback:
            return 0.0

        return ((prices[-1] - prices[-self.lookback]) / prices[-self.lookback]) * 100.0

    def on_bar(self, bar: Bar):
        """Process each bar."""
        symbol = bar.symbol

        if symbol not in self.symbols:
            return

        # Update price history
        self.price_history[symbol].append(bar.close)

        # Keep only what we need
        if len(self.price_history[symbol]) > self.lookback + 1:
            self.price_history[symbol] = self.price_history[symbol][-(self.lookback + 1):]

        # Need enough data
        if len(self.price_history[symbol]) < self.lookback:
            return

        # Check exit conditions first (stop loss / take profit)
        position = self.context.get_position(symbol)

        if position and position.quantity > 0:
            entry_price = self.entry_prices.get(symbol, position.avg_entry_price)

            # Check stop loss
            stop_loss_price = entry_price * (1 - self.stop_loss_pct / 100.0)
            if bar.close <= stop_loss_price:
                print(f"{bar.timestamp}: STOP LOSS - {symbol} at ${bar.close:.2f}")
                print(f"  Entry: ${entry_price:.2f}, Loss: {((bar.close - entry_price) / entry_price * 100):.2f}%")
                self.context.sell(symbol, position.quantity)
                if symbol in self.entry_prices:
                    del self.entry_prices[symbol]
                return

            # Check take profit
            take_profit_price = entry_price * (1 + self.take_profit_pct / 100.0)
            if bar.close >= take_profit_price:
                print(f"{bar.timestamp}: TAKE PROFIT - {symbol} at ${bar.close:.2f}")
                print(f"  Entry: ${entry_price:.2f}, Gain: {((bar.close - entry_price) / entry_price * 100):.2f}%")
                self.context.sell(symbol, position.quantity)
                if symbol in self.entry_prices:
                    del self.entry_prices[symbol]
                return

        # Entry logic - only if we don't have a position
        if not self.context.has_position(symbol):
            momentum = self.calculate_momentum(symbol)

            # Buy if momentum is positive and strong
            if momentum > 5.0:  # 5% momentum threshold
                # Calculate position size based on risk
                position_size = self.context.calculate_position_size(
                    symbol,
                    bar.close,
                    risk_percent=self.risk_per_trade
                )

                # Check if we can afford it
                if position_size > 0 and self.context.can_afford(symbol, position_size, bar.close):
                    # Limit to max 20% of portfolio per position
                    max_position_value = self.context.portfolio_value * 0.20
                    max_shares = int(max_position_value / bar.close)
                    position_size = min(position_size, max_shares)

                    if position_size > 0:
                        print(f"{bar.timestamp}: BUY {position_size} shares of {symbol} at ${bar.close:.2f}")
                        print(f"  Momentum: {momentum:.2f}%")
                        self.context.buy(symbol, position_size)
                        self.entry_prices[symbol] = bar.close

    def on_fill(self, fill_event: FillEvent):
        """React to order fills."""
        order = fill_event.order
        print(f"  FILLED: {order.side.value.upper()} {order.filled_quantity} {order.symbol} @ ${fill_event.fill_price:.2f}")

    def on_stop(self):
        """Called when strategy stops."""
        print(f"\n{self.name} completed")

        # Close all positions
        for position in self.context.get_all_positions():
            if position.quantity > 0:
                print(f"Closing position: {position.symbol} ({position.quantity} shares)")


if __name__ == "__main__":
    # Example: Backtest on multiple tech stocks

    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN"]
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()

    # Create data provider with caching
    data_provider = CachedDataProvider(YahooDataProvider())

    # Create strategy
    strategy = MomentumStrategy(
        symbols=symbols,
        lookback=20,
        risk_per_trade=2.0,
        stop_loss_pct=5.0,
        take_profit_pct=15.0
    )

    # Create backtest engine
    engine = BacktestEngine(
        strategy=strategy,
        data_provider=data_provider,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        initial_cash=100000.0,
        timeframe="1Day"
    )

    # Run backtest
    print("="*60)
    print(f"Backtesting momentum strategy on {len(symbols)} symbols")
    print(f"From {start_date.date()} to {end_date.date()}")
    print("="*60)

    analytics = engine.run(verbose=True)

    # Print detailed report
    print("\n" + analytics.generate_report())
