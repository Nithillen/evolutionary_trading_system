"""
Trading Bot Module
==================
The core autonomous trading agent. Each TradingBot instance is a self-contained
entity with its own strategy parameters, portfolio, and lifecycle state.
"""

import uuid
import logging
from enum import Enum, auto
from typing import Optional

import pandas as pd

from config import SystemConfig
from src.strategies import StrategyParams, SMAMomentumStrategy
from src.portfolio import PortfolioManager

logger = logging.getLogger(__name__)
cfg = SystemConfig()


class BotState(Enum):
    """Lifecycle states for a trading bot."""

    IDLE = auto()
    TRADING = auto()
    KILLED = auto()
    CAPITAL_SECURED = auto()


class TradingBot:
    """
    An autonomous trading agent with its own strategy, portfolio, and lifecycle.

    Lifecycle:
        IDLE -> TRADING -> KILLED (if drawdown) or CAPITAL_SECURED (if profit target hit)

    Attributes:
        bot_id: Unique identifier.
        generation: The evolutionary generation this bot belongs to.
        params: The strategy hyperparameters.
        portfolio: The bot's paper-trading portfolio.
        state: The current lifecycle state.
    """

    def __init__(
        self,
        generation: int,
        params: StrategyParams,
        initial_capital: float,
        ticker: str,
    ):
        self.bot_id: str = uuid.uuid4().hex[:8]
        self.generation: int = generation
        self.params: StrategyParams = params
        self.ticker: str = ticker
        self.initial_capital: float = initial_capital
        self.portfolio: PortfolioManager = PortfolioManager(initial_capital)
        self.strategy: SMAMomentumStrategy = SMAMomentumStrategy(params)
        self.state: BotState = BotState.IDLE
        self.bars_processed: int = 0
        self._peak_value: float = initial_capital

        logger.info(
            f"🤖 [BOT SPAWNED] Bot#{self.bot_id} | Gen {self.generation} | "
            f"Capital: ${initial_capital:.2f} | Ticker: {self.ticker} | "
            f"Params: {self.params.to_dict()}"
        )

    @property
    def is_alive(self) -> bool:
        return self.state == BotState.TRADING

    def start(self) -> None:
        """Transitions the bot from IDLE to TRADING."""
        self.state = BotState.TRADING
        logger.info(f"▶️  [BOT STARTED] Bot#{self.bot_id} is now actively trading.")

    def process_bar(self, bar: pd.Series, historical_data: Optional[pd.DataFrame]) -> Optional[str]:
        """
        Processes a single market data bar.

        Steps:
            1. Generate a signal from the strategy.
            2. Execute the trade if applicable.
            3. Check kill switch and profit target.

        Args:
            bar: The current market data bar (must have 'close' field).
            historical_data: Rolling historical window for indicator calculation.

        Returns:
            "KILLED" if the bot was killed, "SECURED" if capital was secured, None otherwise.
        """
        if not self.is_alive:
            return None

        self.bars_processed += 1
        current_price = bar["close"]
        current_prices = {self.ticker: current_price}

        # --- 1. Generate Signal ---
        signal = self.strategy.generate_signal(historical_data)

        # --- 2. Execute Trade ---
        if signal == 1:  # BUY
            self.portfolio.execute_buy(self.ticker, current_price)
        elif signal == -1:  # SELL
            self.portfolio.execute_sell(self.ticker, current_price)

        # --- 3. Evaluate Portfolio ---
        portfolio_value = self.portfolio.get_portfolio_value(current_prices)

        # Track peak for drawdown calculation
        if portfolio_value > self._peak_value:
            self._peak_value = portfolio_value

        # --- Kill Switch ---
        if portfolio_value <= cfg.KILL_THRESHOLD:
            return self._kill(current_prices)

        # --- Profit Target ---
        if portfolio_value >= cfg.PROFIT_TARGET:
            return self._secure_capital(current_prices)

        return None

    def _kill(self, current_prices: dict[str, float]) -> str:
        """Triggers the kill switch. Liquidates all positions."""
        self.portfolio.liquidate_all(current_prices)
        self.state = BotState.KILLED
        logger.warning(
            f"💀 [BOT KILLED - DRAWDOWN REACHED] Bot#{self.bot_id} | "
            f"Remaining Cash: ${self.portfolio.cash:.4f} | "
            f"Bars Processed: {self.bars_processed}"
        )
        return "KILLED"

    def _secure_capital(self, current_prices: dict[str, float]) -> str:
        """Triggers the capital securing mechanism. Liquidates and splits capital."""
        self.portfolio.liquidate_all(current_prices)
        self.state = BotState.CAPITAL_SECURED
        logger.info(
            f"🔒 [CAPITAL SECURED - TRADING WITH PROFITS] Bot#{self.bot_id} | "
            f"Total Value: ${self.portfolio.cash:.4f} | "
            f"Bars Processed: {self.bars_processed}"
        )
        return "SECURED"

    def get_remaining_capital(self) -> float:
        """Returns the cash available after the bot has been stopped."""
        return self.portfolio.cash

    def get_report(self, current_prices: dict[str, float]) -> str:
        """Returns a formatted summary of the bot's status."""
        lines = [
            f"--- Bot#{self.bot_id} Report (Gen {self.generation}) ---",
            f"  State: {self.state.name}",
            f"  Ticker: {self.ticker}",
            f"  Bars Processed: {self.bars_processed}",
            self.portfolio.get_summary(current_prices),
            f"  Strategy Params: {self.params.to_dict()}",
        ]
        return "\n".join(lines)
