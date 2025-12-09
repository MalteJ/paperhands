"""Performance analytics for backtesting."""

import numpy as np
import pandas as pd
from typing import Dict, List

from ..portfolio.portfolio import Portfolio


class PerformanceAnalytics:
    """
    Calculate performance metrics for a backtest.

    Includes metrics like Sharpe ratio, max drawdown, win rate, etc.
    """

    def __init__(self, portfolio: Portfolio):
        """
        Initialize analytics.

        Args:
            portfolio: Portfolio to analyze
        """
        self.portfolio = portfolio

    def calculate_metrics(self) -> Dict:
        """
        Calculate all performance metrics.

        Returns:
            Dictionary of metrics
        """
        equity_curve = self._get_equity_series()

        metrics = {
            "total_return": self._calculate_total_return(),
            "total_return_percent": self._calculate_total_return_percent(),
            "sharpe_ratio": self._calculate_sharpe_ratio(equity_curve),
            "sortino_ratio": self._calculate_sortino_ratio(equity_curve),
            "max_drawdown": self._calculate_max_drawdown(equity_curve),
            "max_drawdown_duration": self._calculate_max_drawdown_duration(equity_curve),
            "win_rate": self._calculate_win_rate(),
            "profit_factor": self._calculate_profit_factor(),
            "total_trades": len(self.portfolio.trade_history),
            "avg_trade_pnl": self._calculate_avg_trade_pnl(),
            "avg_win": self._calculate_avg_win(),
            "avg_loss": self._calculate_avg_loss(),
            "largest_win": self._calculate_largest_win(),
            "largest_loss": self._calculate_largest_loss(),
        }

        return metrics

    def _get_equity_series(self) -> pd.Series:
        """Get equity as a pandas Series."""
        if not self.portfolio.equity_history:
            return pd.Series(dtype=float)

        df = pd.DataFrame(self.portfolio.equity_history, columns=['timestamp', 'equity'])
        df.set_index('timestamp', inplace=True)
        return df['equity']

    def _calculate_total_return(self) -> float:
        """Calculate total dollar return."""
        return self.portfolio.portfolio_value - self.portfolio.initial_cash

    def _calculate_total_return_percent(self) -> float:
        """Calculate total percentage return."""
        if self.portfolio.initial_cash == 0:
            return 0.0
        return (self._calculate_total_return() / self.portfolio.initial_cash) * 100.0

    def _calculate_sharpe_ratio(self, equity: pd.Series, risk_free_rate: float = 0.0,
                               periods_per_year: int = 252) -> float:
        """
        Calculate Sharpe ratio.

        Args:
            equity: Equity curve
            risk_free_rate: Annual risk-free rate (default 0)
            periods_per_year: Trading periods per year (252 for daily)

        Returns:
            Sharpe ratio
        """
        if len(equity) < 2:
            return 0.0

        returns = equity.pct_change().dropna()

        if len(returns) == 0 or returns.std() == 0:
            return 0.0

        excess_returns = returns - (risk_free_rate / periods_per_year)
        sharpe = np.sqrt(periods_per_year) * (excess_returns.mean() / returns.std())

        return float(sharpe)

    def _calculate_sortino_ratio(self, equity: pd.Series, risk_free_rate: float = 0.0,
                                 periods_per_year: int = 252) -> float:
        """
        Calculate Sortino ratio (uses downside deviation instead of total volatility).

        Args:
            equity: Equity curve
            risk_free_rate: Annual risk-free rate (default 0)
            periods_per_year: Trading periods per year

        Returns:
            Sortino ratio
        """
        if len(equity) < 2:
            return 0.0

        returns = equity.pct_change().dropna()

        if len(returns) == 0:
            return 0.0

        # Calculate downside deviation (only negative returns)
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0

        excess_returns = returns - (risk_free_rate / periods_per_year)
        sortino = np.sqrt(periods_per_year) * (excess_returns.mean() / downside_returns.std())

        return float(sortino)

    def _calculate_max_drawdown(self, equity: pd.Series) -> float:
        """
        Calculate maximum drawdown percentage.

        Args:
            equity: Equity curve

        Returns:
            Max drawdown as percentage
        """
        if len(equity) < 2:
            return 0.0

        cummax = equity.expanding(min_periods=1).max()
        drawdown = (equity - cummax) / cummax * 100.0

        return float(drawdown.min())

    def _calculate_max_drawdown_duration(self, equity: pd.Series) -> int:
        """
        Calculate maximum drawdown duration in periods.

        Args:
            equity: Equity curve

        Returns:
            Max drawdown duration
        """
        if len(equity) < 2:
            return 0

        cummax = equity.expanding(min_periods=1).max()
        drawdown = equity - cummax

        # Find periods where we're in drawdown
        in_drawdown = drawdown < 0

        # Calculate duration of each drawdown period
        max_duration = 0
        current_duration = 0

        for is_dd in in_drawdown:
            if is_dd:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0

        return max_duration

    def _get_trade_pnls(self) -> List[float]:
        """Calculate P&L for each round-trip trade."""
        # This is simplified - tracks per-trade basis
        trades = self.portfolio.trade_history

        if not trades:
            return []

        # Group trades by symbol and calculate P&L
        pnls = []
        positions = {}

        for trade in trades:
            symbol = trade['symbol']
            if symbol not in positions:
                positions[symbol] = {'quantity': 0, 'cost_basis': 0.0}

            pos = positions[symbol]

            if trade['side'] == 'buy':
                # Update position
                total_cost = pos['cost_basis'] * abs(pos['quantity']) + trade['price'] * trade['quantity']
                pos['quantity'] += trade['quantity']
                if pos['quantity'] != 0:
                    pos['cost_basis'] = total_cost / abs(pos['quantity'])
            else:  # sell
                if pos['quantity'] > 0:
                    # Closing long
                    pnl = (trade['price'] - pos['cost_basis']) * trade['quantity']
                    pnls.append(pnl)

                    pos['quantity'] -= trade['quantity']

        return pnls

    def _calculate_win_rate(self) -> float:
        """Calculate win rate percentage."""
        pnls = self._get_trade_pnls()

        if not pnls:
            return 0.0

        wins = sum(1 for pnl in pnls if pnl > 0)
        return (wins / len(pnls)) * 100.0

    def _calculate_profit_factor(self) -> float:
        """Calculate profit factor (gross wins / gross losses)."""
        pnls = self._get_trade_pnls()

        if not pnls:
            return 0.0

        wins = sum(pnl for pnl in pnls if pnl > 0)
        losses = abs(sum(pnl for pnl in pnls if pnl < 0))

        if losses == 0:
            return float('inf') if wins > 0 else 0.0

        return wins / losses

    def _calculate_avg_trade_pnl(self) -> float:
        """Calculate average P&L per trade."""
        pnls = self._get_trade_pnls()
        return sum(pnls) / len(pnls) if pnls else 0.0

    def _calculate_avg_win(self) -> float:
        """Calculate average winning trade."""
        pnls = self._get_trade_pnls()
        wins = [pnl for pnl in pnls if pnl > 0]
        return sum(wins) / len(wins) if wins else 0.0

    def _calculate_avg_loss(self) -> float:
        """Calculate average losing trade."""
        pnls = self._get_trade_pnls()
        losses = [pnl for pnl in pnls if pnl < 0]
        return sum(losses) / len(losses) if losses else 0.0

    def _calculate_largest_win(self) -> float:
        """Calculate largest winning trade."""
        pnls = self._get_trade_pnls()
        wins = [pnl for pnl in pnls if pnl > 0]
        return max(wins) if wins else 0.0

    def _calculate_largest_loss(self) -> float:
        """Calculate largest losing trade."""
        pnls = self._get_trade_pnls()
        losses = [pnl for pnl in pnls if pnl < 0]
        return min(losses) if losses else 0.0

    def generate_report(self) -> str:
        """
        Generate a text report of performance metrics.

        Returns:
            Formatted report string
        """
        metrics = self.calculate_metrics()

        report = []
        report.append("=" * 60)
        report.append("PERFORMANCE REPORT")
        report.append("=" * 60)
        report.append("")
        report.append("Returns:")
        report.append(f"  Total Return:        ${metrics['total_return']:,.2f}")
        report.append(f"  Total Return %:      {metrics['total_return_percent']:.2f}%")
        report.append("")
        report.append("Risk Metrics:")
        report.append(f"  Sharpe Ratio:        {metrics['sharpe_ratio']:.2f}")
        report.append(f"  Sortino Ratio:       {metrics['sortino_ratio']:.2f}")
        report.append(f"  Max Drawdown:        {metrics['max_drawdown']:.2f}%")
        report.append(f"  Max DD Duration:     {metrics['max_drawdown_duration']} periods")
        report.append("")
        report.append("Trade Statistics:")
        report.append(f"  Total Trades:        {metrics['total_trades']}")
        report.append(f"  Win Rate:            {metrics['win_rate']:.2f}%")
        report.append(f"  Profit Factor:       {metrics['profit_factor']:.2f}")
        report.append(f"  Avg Trade P&L:       ${metrics['avg_trade_pnl']:,.2f}")
        report.append(f"  Avg Win:             ${metrics['avg_win']:,.2f}")
        report.append(f"  Avg Loss:            ${metrics['avg_loss']:,.2f}")
        report.append(f"  Largest Win:         ${metrics['largest_win']:,.2f}")
        report.append(f"  Largest Loss:        ${metrics['largest_loss']:,.2f}")
        report.append("=" * 60)

        return "\n".join(report)
