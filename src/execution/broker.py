"""Abstract broker interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..core.types import Order, OrderStatus, Position


class Broker(ABC):
    """
    Abstract interface for order execution.

    This allows strategies to submit orders without knowing whether
    they're running in backtest or live mode.
    """

    @abstractmethod
    def submit_order(self, order: Order) -> Order:
        """
        Submit an order for execution.

        Args:
            order: Order to submit

        Returns:
            Order with order_id and updated status
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order.

        Args:
            order_id: ID of order to cancel

        Returns:
            True if successfully canceled
        """
        pass

    @abstractmethod
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get order by ID.

        Args:
            order_id: Order ID

        Returns:
            Order object or None
        """
        pass

    @abstractmethod
    def get_open_orders(self) -> List[Order]:
        """
        Get all open orders.

        Returns:
            List of open orders
        """
        pass

    @abstractmethod
    def get_positions(self) -> List[Position]:
        """
        Get all current positions.

        Returns:
            List of positions
        """
        pass

    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a specific symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            Position or None
        """
        pass
