"""
Portfolio Manager Module
========================
Manages the virtual paper-trading portfolio for a single TradingBot instance.
Tracks cash, positions, trade history, and portfolio valuation.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from config import SystemConfig

logger = logging.getLogger(__name__)
cfg = SystemConfig()


@dataclass
class Trade:
    """Immutable record of an executed trade."""

    timestamp: str
    ticker: str
    side: str  # "BUY" or "SELL"
    quantity: float
    price: float
    fee: float
    pnl: Optional[float] = None  # Realized P&L (only for closing trades)

    def __str__(self) -> str:
        pnl_str = f" | PnL: ${self.pnl:+.4f}" if self.pnl is not None else ""
        return (
            f"[{self.timestamp}] {self.side} {self.quantity:.6f} {self.ticker} "
            f"@ ${self.price:.2f} (fee: ${self.fee:.4f}){pnl_str}"
        )


class PortfolioManager:
    """
    Manages the virtual cash balance, open positions, and trade execution
    for a single trading bot.

    Attributes:
        cash: Current available cash balance.
        positions: Dict mapping ticker -> quantity held.
        trade_log: List of all executed Trade records.
    """

    def __init__(self, initial_cash: float):
        self.cash: float = initial_cash
        self.positions: dict[str, float] = {}  # ticker -> quantity
        self._entry_prices: dict[str, float] = {}  # ticker -> avg entry price
        self.trade_log: List[Trade] = []

    @property
    def total_trades(self) -> int:
        return len(self.trade_log)

    def get_portfolio_value(self, current_prices: dict[str, float]) -> float:
        """
        Calculates the total portfolio value (cash + market value of all positions).

        Args:
            current_prices: Dict mapping ticker -> current market price.

        Returns:
            Total portfolio value in dollars.
        """
        position_value = sum(
            qty * current_prices.get(ticker, 0.0) for ticker, qty in self.positions.items()
        )
        return self.cash + position_value

    def execute_buy(self, ticker: str, price: float, allocation_pct: float = 0.95) -> Optional[Trade]:
        """
        Executes a BUY order, allocating a percentage of available cash.

        Args:
            ticker: The asset to buy.
            price: The current market price.
            allocation_pct: Fraction of cash to allocate (default 95% to reserve for fees).

        Returns:
            The Trade object if executed, or None if insufficient funds.
        """
        available = self.cash * allocation_pct
        fee = available * cfg.TRANSACTION_FEE_PCT
        net_amount = available - fee
        quantity = net_amount / price

        if quantity <= 0 or net_amount <= 0:
            return None

        self.cash -= (net_amount + fee)
        self.positions[ticker] = self.positions.get(ticker, 0.0) + quantity
        self._entry_prices[ticker] = price  # Simplified: last entry price

        trade = Trade(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ticker=ticker,
            side="BUY",
            quantity=quantity,
            price=price,
            fee=fee,
        )
        self.trade_log.append(trade)
        logger.info(f"📈 [TRADE EXECUTED] {trade}")
        return trade

    def execute_sell(self, ticker: str, price: float) -> Optional[Trade]:
        """
        Executes a SELL order, liquidating the entire position in the given ticker.

        Args:
            ticker: The asset to sell.
            price: The current market price.

        Returns:
            The Trade object if executed, or None if no position exists.
        """
        quantity = self.positions.get(ticker, 0.0)
        if quantity <= 0:
            return None

        gross_proceeds = quantity * price
        fee = gross_proceeds * cfg.TRANSACTION_FEE_PCT
        net_proceeds = gross_proceeds - fee

        # Calculate realized PnL
        entry_price = self._entry_prices.get(ticker, price)
        pnl = (price - entry_price) * quantity - fee

        self.cash += net_proceeds
        del self.positions[ticker]
        if ticker in self._entry_prices:
            del self._entry_prices[ticker]

        trade = Trade(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ticker=ticker,
            side="SELL",
            quantity=quantity,
            price=price,
            fee=fee,
            pnl=pnl,
        )
        self.trade_log.append(trade)
        logger.info(f"📉 [TRADE EXECUTED] {trade}")
        return trade

    def liquidate_all(self, current_prices: dict[str, float]) -> float:
        """
        Liquidates all open positions at current market prices.

        Returns:
            The total cash after liquidation.
        """
        tickers_to_sell = list(self.positions.keys())
        for ticker in tickers_to_sell:
            price = current_prices.get(ticker)
            if price:
                self.execute_sell(ticker, price)
        return self.cash

    def get_summary(self, current_prices: dict[str, float]) -> str:
        """Returns a formatted summary of the portfolio state."""
        value = self.get_portfolio_value(current_prices)
        lines = [
            f"  Cash: ${self.cash:.4f}",
            f"  Positions: {self.positions}",
            f"  Portfolio Value: ${value:.4f}",
            f"  Total Trades: {self.total_trades}",
        ]
        return "\n".join(lines)
