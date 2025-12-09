"""Strategy context provides access to market data, portfolio, and execution."""

from datetime import datetime
from typing import Optional, List
import pandas as pd

from ..core.types import Order, Position, OrderType, OrderSide, TimeInForce, Bar
from ..execution.broker import Broker
from ..portfolio.portfolio import Portfolio
from ..data.provider import DataProvider


class StrategyContext:
    """
    Context object passed to strategies.

    This abstraction allows the same strategy code to work in both
    backtesting and live trading modes. The strategy only interacts
    with this context, never directly with the underlying systems.
    """

    def __init__(self, broker: Broker, portfolio: Portfolio, data_provider: DataProvider):
        """
        Initialize strategy context.

        Args:
            broker: Broker for order execution
            portfolio: Portfolio for position/cash tracking
            data_provider: Data provider for historical/current data
        """
        self.broker = broker
        self.portfolio = portfolio
        self.data_provider = data_provider

        # Current timestamp (set by backtesting engine or live runner)
        self.current_time: Optional[datetime] = None

    # ========== Portfolio queries ==========

    @property
    def cash(self) -> float:
        """Get available cash."""
        return self.portfolio.cash

    @property
    def portfolio_value(self) -> float:
        """Get total portfolio value."""
        return self.portfolio.portfolio_value

    @property
    def buying_power(self) -> float:
        """Get available buying power."""
        return self.portfolio.get_buying_power()

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            Position or None
        """
        return self.portfolio.get_position(symbol)

    def get_position_size(self, symbol: str) -> int:
        """
        Get position size for a symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            Position size (positive for long, negative for short)
        """
        return self.portfolio.get_position_size(symbol)

    def has_position(self, symbol: str) -> bool:
        """
        Check if we have a position in a symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            True if position exists
        """
        return self.portfolio.has_position(symbol)

    def get_all_positions(self) -> List[Position]:
        """Get all current positions."""
        return self.portfolio.get_all_positions()

    # ========== Order submission ==========

    def buy(self, symbol: str, quantity: int, order_type: OrderType = OrderType.MARKET,
            limit_price: Optional[float] = None, stop_price: Optional[float] = None,
            time_in_force: TimeInForce = TimeInForce.DAY) -> Order:
        """
        Submit a buy order.

        Args:
            symbol: Ticker symbol
            quantity: Number of shares
            order_type: Type of order (default MARKET)
            limit_price: Limit price for limit orders
            stop_price: Stop price for stop orders
            time_in_force: Time in force (default DAY)

        Returns:
            Submitted order
        """
        order = Order(
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            stop_price=stop_price,
            time_in_force=time_in_force
        )
        return self.broker.submit_order(order)

    def sell(self, symbol: str, quantity: int, order_type: OrderType = OrderType.MARKET,
             limit_price: Optional[float] = None, stop_price: Optional[float] = None,
             time_in_force: TimeInForce = TimeInForce.DAY) -> Order:
        """
        Submit a sell order.

        Args:
            symbol: Ticker symbol
            quantity: Number of shares
            order_type: Type of order (default MARKET)
            limit_price: Limit price for limit orders
            stop_price: Stop price for stop orders
            time_in_force: Time in force (default DAY)

        Returns:
            Submitted order
        """
        order = Order(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            stop_price=stop_price,
            time_in_force=time_in_force
        )
        return self.broker.submit_order(order)

    def submit_order(self, order: Order) -> Order:
        """
        Submit a custom order.

        Args:
            order: Order to submit

        Returns:
            Submitted order
        """
        return self.broker.submit_order(order)

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: ID of order to cancel

        Returns:
            True if successfully canceled
        """
        return self.broker.cancel_order(order_id)

    def get_open_orders(self) -> List[Order]:
        """Get all open orders."""
        return self.broker.get_open_orders()

    # ========== Data access ==========

    def get_latest_bar(self, symbol: str) -> Optional[Bar]:
        """
        Get the most recent bar for a symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            Latest bar or None
        """
        return self.data_provider.get_latest_bar(symbol)

    def get_historical_bars(self, symbol: str, start: datetime, end: datetime,
                           timeframe: str = "1Day") -> List[Bar]:
        """
        Get historical bars.

        Args:
            symbol: Ticker symbol
            start: Start datetime
            end: End datetime
            timeframe: Timeframe (e.g., "1Hour", "1Day")

        Returns:
            List of bars
        """
        return self.data_provider.get_bars(symbol, start, end, timeframe)

    def get_historical_df(self, symbol: str, start: datetime, end: datetime,
                         timeframe: str = "1Day") -> pd.DataFrame:
        """
        Get historical data as DataFrame.

        Args:
            symbol: Ticker symbol
            start: Start datetime
            end: End datetime
            timeframe: Timeframe (e.g., "1Hour", "1Day")

        Returns:
            DataFrame with OHLCV data
        """
        return self.data_provider.get_bars_df(symbol, start, end, timeframe)

    # ========== Position sizing helpers ==========

    def calculate_position_size(self, symbol: str, price: float,
                                risk_percent: float = 2.0) -> int:
        """
        Calculate position size based on portfolio risk.

        Args:
            symbol: Ticker symbol
            price: Entry price
            risk_percent: Percentage of portfolio to risk (default 2%)

        Returns:
            Number of shares to buy
        """
        risk_amount = self.portfolio_value * (risk_percent / 100.0)
        shares = int(risk_amount / price)
        return max(1, shares)

    def calculate_position_size_fixed_amount(self, price: float, amount: float) -> int:
        """
        Calculate position size for a fixed dollar amount.

        Args:
            price: Entry price
            amount: Dollar amount to invest

        Returns:
            Number of shares to buy
        """
        return int(amount / price)

    def can_afford(self, symbol: str, quantity: int, price: float) -> bool:
        """
        Check if we can afford a purchase.

        Args:
            symbol: Ticker symbol
            quantity: Number of shares
            price: Price per share

        Returns:
            True if affordable
        """
        return self.portfolio.can_afford(symbol, quantity, price)
