"""Portfolio management and tracking."""

from datetime import datetime
from typing import Dict, Optional, List
from collections import defaultdict

from ..core.types import Position, Order, OrderSide


class Portfolio:
    """
    Manages portfolio state including cash, positions, and equity tracking.

    This class is used by both backtesting and live trading to maintain
    a consistent view of the portfolio state.
    """

    def __init__(self, initial_cash: float = 100000.0):
        """
        Initialize portfolio.

        Args:
            initial_cash: Starting cash balance
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, Position] = {}

        # Track equity over time
        self.equity_history: List[tuple[datetime, float]] = []

        # Track realized P&L
        self.realized_pnl = 0.0

        # Track trade history
        self.trade_history: List[dict] = []

    @property
    def portfolio_value(self) -> float:
        """
        Calculate total portfolio value (cash + positions).

        Returns:
            Total portfolio value
        """
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value

    @property
    def positions_value(self) -> float:
        """
        Calculate total value of all positions.

        Returns:
            Sum of all position values
        """
        return sum(pos.market_value for pos in self.positions.values())

    @property
    def total_pnl(self) -> float:
        """
        Calculate total profit/loss (realized + unrealized).

        Returns:
            Total P&L
        """
        unrealized = sum(pos.unrealized_pnl for pos in self.positions.values())
        return self.realized_pnl + unrealized

    @property
    def total_pnl_percent(self) -> float:
        """
        Calculate total P&L as a percentage of initial capital.

        Returns:
            Total P&L percentage
        """
        if self.initial_cash == 0:
            return 0.0
        return (self.total_pnl / self.initial_cash) * 100.0

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            Position object or None if no position exists
        """
        return self.positions.get(symbol)

    def has_position(self, symbol: str) -> bool:
        """
        Check if portfolio has a position in a symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            True if position exists
        """
        return symbol in self.positions and self.positions[symbol].quantity != 0

    def update_position_prices(self, prices: Dict[str, float], timestamp: datetime = None):
        """
        Update current prices for all positions.

        Args:
            prices: Dictionary mapping symbols to current prices
            timestamp: Optional timestamp for equity tracking
        """
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.current_price = prices[symbol]

        # Record equity if timestamp provided
        if timestamp:
            self.equity_history.append((timestamp, self.portfolio_value))

    def process_fill(self, order: Order, fill_price: float, commission: float = 0.0,
                    timestamp: datetime = None):
        """
        Process an order fill and update portfolio state.

        Args:
            order: The filled order
            fill_price: Price at which order was filled
            commission: Commission paid
            timestamp: Time of fill
        """
        symbol = order.symbol
        quantity = order.quantity if order.side == OrderSide.BUY else -order.quantity

        # Calculate transaction cost
        transaction_cost = fill_price * abs(quantity) + commission

        # Update or create position
        if symbol in self.positions:
            position = self.positions[symbol]
            old_quantity = position.quantity

            # Calculate new average price
            if (old_quantity > 0 and quantity > 0) or (old_quantity < 0 and quantity < 0):
                # Adding to existing position
                total_cost = position.avg_entry_price * abs(old_quantity) + fill_price * abs(quantity)
                new_quantity = old_quantity + quantity
                position.avg_entry_price = total_cost / abs(new_quantity)
                position.quantity = new_quantity
            elif old_quantity + quantity == 0:
                # Closing position completely
                realized = (fill_price - position.avg_entry_price) * abs(quantity)
                if old_quantity < 0:  # Was short, reversing sign
                    realized = -realized
                self.realized_pnl += realized
                del self.positions[symbol]
            else:
                # Partially closing or reversing position
                if abs(quantity) < abs(old_quantity):
                    # Partially closing
                    realized = (fill_price - position.avg_entry_price) * abs(quantity)
                    if old_quantity < 0:
                        realized = -realized
                    self.realized_pnl += realized
                    position.quantity = old_quantity + quantity
                else:
                    # Reversing position
                    realized = (fill_price - position.avg_entry_price) * abs(old_quantity)
                    if old_quantity < 0:
                        realized = -realized
                    self.realized_pnl += realized

                    # Create new position in opposite direction
                    remaining_quantity = quantity + old_quantity
                    position.quantity = remaining_quantity
                    position.avg_entry_price = fill_price

            position.current_price = fill_price
        else:
            # New position
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_entry_price=fill_price,
                current_price=fill_price
            )

        # Update cash
        if order.side == OrderSide.BUY:
            self.cash -= transaction_cost
        else:
            self.cash += (fill_price * order.quantity - commission)

        # Record trade
        self.trade_history.append({
            "timestamp": timestamp,
            "symbol": symbol,
            "side": order.side.value,
            "quantity": order.quantity,
            "price": fill_price,
            "commission": commission,
            "cash_after": self.cash,
            "portfolio_value": self.portfolio_value
        })

    def get_buying_power(self) -> float:
        """
        Get available buying power.

        For now, this is just cash. In the future, this could include
        margin calculations.

        Returns:
            Available buying power
        """
        return self.cash

    def can_afford(self, symbol: str, quantity: int, price: float) -> bool:
        """
        Check if portfolio can afford a purchase.

        Args:
            symbol: Ticker symbol
            quantity: Number of shares
            price: Price per share

        Returns:
            True if purchase is affordable
        """
        cost = quantity * price
        return self.cash >= cost

    def get_position_size(self, symbol: str) -> int:
        """
        Get current position size for a symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            Position size (positive for long, negative for short, 0 for no position)
        """
        if symbol in self.positions:
            return self.positions[symbol].quantity
        return 0

    def get_all_positions(self) -> List[Position]:
        """
        Get all current positions.

        Returns:
            List of Position objects
        """
        return [pos for pos in self.positions.values() if pos.quantity != 0]

    def summary(self) -> dict:
        """
        Get portfolio summary.

        Returns:
            Dictionary with portfolio metrics
        """
        return {
            "cash": self.cash,
            "positions_value": self.positions_value,
            "portfolio_value": self.portfolio_value,
            "total_pnl": self.total_pnl,
            "total_pnl_percent": self.total_pnl_percent,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": sum(pos.unrealized_pnl for pos in self.positions.values()),
            "num_positions": len([p for p in self.positions.values() if p.quantity != 0]),
            "return_percent": ((self.portfolio_value - self.initial_cash) / self.initial_cash) * 100.0
        }
