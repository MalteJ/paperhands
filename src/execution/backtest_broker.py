"""Simulated broker for backtesting."""

from datetime import datetime
from typing import List, Optional, Dict
import uuid

from .broker import Broker
from ..core.types import Order, OrderStatus, OrderSide, OrderType, Position
from ..core.events import FillEvent
from ..portfolio.portfolio import Portfolio


class BacktestBroker(Broker):
    """
    Simulated broker for backtesting.

    Handles order simulation, fill logic, and commission calculations.
    """

    def __init__(self, portfolio: Portfolio, commission_per_share: float = 0.0,
                 slippage_percent: float = 0.0):
        """
        Initialize backtest broker.

        Args:
            portfolio: Portfolio to manage
            commission_per_share: Commission per share (default 0 for commission-free)
            slippage_percent: Simulated slippage as percentage (default 0)
        """
        self.portfolio = portfolio
        self.commission_per_share = commission_per_share
        self.slippage_percent = slippage_percent

        # Track orders
        self.orders: Dict[str, Order] = {}
        self.open_orders: List[Order] = []

        # Track fills for event emission
        self.fill_events: List[FillEvent] = []

    def submit_order(self, order: Order) -> Order:
        """Submit an order in the backtest."""
        # Generate order ID
        order.order_id = str(uuid.uuid4())
        order.status = OrderStatus.SUBMITTED
        order.submitted_at = datetime.now()

        # Store order
        self.orders[order.order_id] = order
        self.open_orders.append(order)

        return order

    def process_bar(self, symbol: str, bar_open: float, bar_high: float,
                   bar_low: float, bar_close: float, timestamp: datetime):
        """
        Process a bar and check if any orders should be filled.

        Args:
            symbol: Symbol of the bar
            bar_open: Open price
            bar_high: High price
            bar_low: Low price
            bar_close: Close price
            timestamp: Bar timestamp
        """
        # Check all open orders for this symbol
        orders_to_remove = []

        for order in self.open_orders:
            if order.symbol != symbol:
                continue

            filled = False
            fill_price = None

            if order.order_type == OrderType.MARKET:
                # Market orders fill at open price (realistic for backtesting)
                fill_price = bar_open
                filled = True

            elif order.order_type == OrderType.LIMIT:
                if order.side == OrderSide.BUY:
                    # Buy limit: fill if bar went at or below limit price
                    if bar_low <= order.limit_price:
                        fill_price = min(order.limit_price, bar_open)
                        filled = True
                else:  # SELL
                    # Sell limit: fill if bar went at or above limit price
                    if bar_high >= order.limit_price:
                        fill_price = max(order.limit_price, bar_open)
                        filled = True

            elif order.order_type == OrderType.STOP:
                if order.side == OrderSide.BUY:
                    # Buy stop: fill if bar went at or above stop price
                    if bar_high >= order.stop_price:
                        fill_price = max(order.stop_price, bar_open)
                        filled = True
                else:  # SELL
                    # Sell stop: fill if bar went at or below stop price
                    if bar_low <= order.stop_price:
                        fill_price = min(order.stop_price, bar_open)
                        filled = True

            if filled and fill_price is not None:
                # Apply slippage
                if self.slippage_percent > 0:
                    slippage = fill_price * (self.slippage_percent / 100.0)
                    if order.side == OrderSide.BUY:
                        fill_price += slippage
                    else:
                        fill_price -= slippage

                # Calculate commission
                commission = order.quantity * self.commission_per_share

                # Update order status
                order.status = OrderStatus.FILLED
                order.filled_at = timestamp
                order.filled_quantity = order.quantity
                order.filled_avg_price = fill_price

                # Process fill in portfolio
                self.portfolio.process_fill(order, fill_price, commission, timestamp)

                # Create fill event
                fill_event = FillEvent(
                    order=order,
                    fill_price=fill_price,
                    fill_quantity=order.quantity,
                    timestamp=timestamp,
                    commission=commission
                )
                self.fill_events.append(fill_event)

                # Mark for removal from open orders
                orders_to_remove.append(order)

        # Remove filled orders
        for order in orders_to_remove:
            self.open_orders.remove(order)

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        if order_id not in self.orders:
            return False

        order = self.orders[order_id]
        if order.status not in (OrderStatus.SUBMITTED, OrderStatus.PENDING):
            return False

        order.status = OrderStatus.CANCELED
        if order in self.open_orders:
            self.open_orders.remove(order)

        return True

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self.orders.get(order_id)

    def get_open_orders(self) -> List[Order]:
        """Get all open orders."""
        return self.open_orders.copy()

    def get_positions(self) -> List[Position]:
        """Get all positions from portfolio."""
        return self.portfolio.get_all_positions()

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a symbol."""
        return self.portfolio.get_position(symbol)

    def get_fill_events(self) -> List[FillEvent]:
        """
        Get and clear fill events since last call.

        Returns:
            List of fill events
        """
        events = self.fill_events.copy()
        self.fill_events.clear()
        return events
