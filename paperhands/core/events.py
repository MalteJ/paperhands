"""Event system for the trading framework."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .types import Bar, Order


class EventType(Enum):
    """Types of events in the system."""
    BAR = "bar"
    ORDER = "order"
    FILL = "fill"


@dataclass
class Event:
    """Base class for all events."""
    timestamp: datetime
    event_type: EventType


@dataclass
class BarEvent(Event):
    """Event fired when a new bar is received."""
    bar: Bar

    def __init__(self, bar: Bar):
        super().__init__(timestamp=bar.timestamp, event_type=EventType.BAR)
        self.bar = bar


@dataclass
class OrderEvent(Event):
    """Event fired when an order is submitted."""
    order: Order

    def __init__(self, order: Order, timestamp: datetime):
        super().__init__(timestamp=timestamp, event_type=EventType.ORDER)
        self.order = order


@dataclass
class FillEvent(Event):
    """Event fired when an order is filled."""
    order: Order
    fill_price: float
    fill_quantity: int
    commission: float = 0.0

    def __init__(self, order: Order, fill_price: float, fill_quantity: int,
                 timestamp: datetime, commission: float = 0.0):
        super().__init__(timestamp=timestamp, event_type=EventType.FILL)
        self.order = order
        self.fill_price = fill_price
        self.fill_quantity = fill_quantity
        self.commission = commission
