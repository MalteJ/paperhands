"""Basic tests to verify the framework is working."""

import unittest
from datetime import datetime, timedelta

from src.core.types import Bar, Order, OrderType, OrderSide, TimeInForce, Position
from src.portfolio.portfolio import Portfolio
from src.execution.backtest_broker import BacktestBroker


class TestCoreTypes(unittest.TestCase):
    """Test core data types."""

    def test_bar_creation(self):
        """Test creating a Bar."""
        bar = Bar(
            timestamp=datetime.now(),
            symbol="SPY",
            open=450.0,
            high=452.0,
            low=449.0,
            close=451.0,
            volume=1000000
        )

        self.assertEqual(bar.symbol, "SPY")
        self.assertEqual(bar.close, 451.0)
        self.assertTrue(bar.typical_price > 0)

    def test_order_creation(self):
        """Test creating an Order."""
        order = Order(
            symbol="SPY",
            side=OrderSide.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )

        self.assertEqual(order.symbol, "SPY")
        self.assertEqual(order.quantity, 100)
        self.assertFalse(order.is_filled)

    def test_position_calculations(self):
        """Test position P&L calculations."""
        position = Position(
            symbol="SPY",
            quantity=100,
            avg_entry_price=450.0,
            current_price=460.0
        )

        self.assertEqual(position.cost_basis, 45000.0)
        self.assertEqual(position.market_value, 46000.0)
        self.assertEqual(position.unrealized_pnl, 1000.0)
        self.assertTrue(position.is_long)


class TestPortfolio(unittest.TestCase):
    """Test portfolio management."""

    def test_portfolio_initialization(self):
        """Test creating a portfolio."""
        portfolio = Portfolio(initial_cash=100000.0)

        self.assertEqual(portfolio.cash, 100000.0)
        self.assertEqual(portfolio.portfolio_value, 100000.0)
        self.assertEqual(len(portfolio.positions), 0)

    def test_portfolio_fill_processing(self):
        """Test processing order fills."""
        portfolio = Portfolio(initial_cash=100000.0)

        # Create a buy order
        order = Order(
            symbol="SPY",
            side=OrderSide.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )

        # Process fill
        portfolio.process_fill(order, fill_price=450.0, commission=0.0)

        # Check portfolio state
        self.assertLess(portfolio.cash, 100000.0)
        self.assertTrue(portfolio.has_position("SPY"))

        position = portfolio.get_position("SPY")
        self.assertEqual(position.quantity, 100)
        self.assertEqual(position.avg_entry_price, 450.0)


class TestBacktestBroker(unittest.TestCase):
    """Test backtest broker simulation."""

    def test_broker_initialization(self):
        """Test creating a backtest broker."""
        portfolio = Portfolio(initial_cash=100000.0)
        broker = BacktestBroker(portfolio)

        self.assertEqual(len(broker.get_open_orders()), 0)

    def test_order_submission(self):
        """Test submitting orders."""
        portfolio = Portfolio(initial_cash=100000.0)
        broker = BacktestBroker(portfolio)

        order = Order(
            symbol="SPY",
            side=OrderSide.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )

        submitted_order = broker.submit_order(order)

        self.assertIsNotNone(submitted_order.order_id)
        self.assertEqual(len(broker.get_open_orders()), 1)

    def test_market_order_fill(self):
        """Test that market orders fill correctly."""
        portfolio = Portfolio(initial_cash=100000.0)
        broker = BacktestBroker(portfolio)

        order = Order(
            symbol="SPY",
            side=OrderSide.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )

        broker.submit_order(order)

        # Process a bar - market order should fill at open
        broker.process_bar(
            symbol="SPY",
            bar_open=450.0,
            bar_high=452.0,
            bar_low=449.0,
            bar_close=451.0,
            timestamp=datetime.now()
        )

        # Order should be filled
        self.assertEqual(len(broker.get_open_orders()), 0)
        self.assertTrue(portfolio.has_position("SPY"))


if __name__ == "__main__":
    unittest.main()
