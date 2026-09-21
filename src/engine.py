"""
Evolutionary Engine Module
==========================
The master controller that orchestrates the evolutionary lifecycle of trading bots.
It spawns bots, feeds them market data, handles kill/secure events,
mutates strategy parameters, and tracks generational performance.
"""

import asyncio
import logging
import random
from typing import List, Optional

from config import SystemConfig
from src.data_feed import MarketDataFeed
from src.bot import TradingBot, BotState
from src.vault import SafeVault
from src.strategies import StrategyParams

logger = logging.getLogger(__name__)
cfg = SystemConfig()


class EvolutionaryEngine:
    """
    The master orchestrator of the evolutionary trading system.

    Responsibilities:
        - Spawns TradingBot instances with randomized parameters.
        - Streams market data bar-by-bar to the active bot.
        - Handles KILLED events: mutates parameters and spawns a successor.
        - Handles SECURED events: deposits initial capital into the SafeVault
          and respawns the bot with only the profit.
        - Tracks statistics across all generations.
    """

    def __init__(self):
        self.vault: SafeVault = SafeVault()
        self.generation: int = 0
        self.active_bot: Optional[TradingBot] = None
        self.bot_history: List[TradingBot] = []
        self.active_capital: float = cfg.INITIAL_CAPITAL

        # Statistics
        self.total_bots_spawned: int = 0
        self.total_bots_killed: int = 0
        self.total_bots_secured: int = 0

    async def run(self, ticker: str) -> None:
        """
        Main execution loop. Runs the evolutionary lifecycle until
        max generations are reached or data is exhausted.

        Args:
            ticker: The stock ticker to trade.
        """
        logger.info("=" * 70)
        logger.info("🚀 EVOLUTIONARY TRADING SYSTEM - STARTING")
        logger.info(f"   Ticker: {ticker}")
        logger.info(f"   Initial Capital: ${cfg.INITIAL_CAPITAL:.2f}")
        logger.info(f"   Kill Threshold: ${cfg.KILL_THRESHOLD:.2f}")
        logger.info(f"   Profit Target: ${cfg.PROFIT_TARGET:.2f}")
        logger.info(f"   Max Generations: {cfg.MAX_GENERATIONS}")
        logger.info("=" * 70)

        # Initialize market data feed
        data_feed = MarketDataFeed(ticker=ticker, interval=cfg.DEFAULT_INTERVAL, period=cfg.DEFAULT_LOOKBACK_PERIOD)
        await data_feed.initialize()

        # Start the first generation
        params = StrategyParams.random()
        self._spawn_bot(params, self.active_capital, ticker)

        # Main loop
        while self.generation < cfg.MAX_GENERATIONS and data_feed.bars_remaining > 0:
            bar = await data_feed.get_next_bar()
            if bar is None:
                logger.info("📊 Data stream exhausted.")
                break

            # Get historical window for indicators (avoid look-ahead bias)
            lookback = max(cfg.SMA_SLOW_RANGE[1], cfg.RSI_PERIOD_RANGE[1]) + 10
            historical = data_feed.get_historical_window(lookback)

            # Process the bar
            result = self.active_bot.process_bar(bar, historical)

            # Handle lifecycle events
            if result == "KILLED":
                self.total_bots_killed += 1
                remaining = self.active_bot.get_remaining_capital()
                self.bot_history.append(self.active_bot)

                if remaining < 0.50:
                    logger.error(
                        f"⛔ Remaining capital (${remaining:.2f}) is too low to continue. Stopping evolution."
                    )
                    break

                # Mutate and respawn
                mutated_params = self.active_bot.params.mutate(rate=cfg.MUTATION_RATE)
                self.active_capital = remaining
                self._spawn_bot(mutated_params, self.active_capital, ticker)

                # Reset data stream to give the new bot a fresh start at the same point
                # (It continues from where the previous bot died — no look-ahead)

            elif result == "SECURED":
                self.total_bots_secured += 1
                total_cash = self.active_bot.get_remaining_capital()
                self.bot_history.append(self.active_bot)

                # Secure the initial capital into the vault
                secure_amount = min(cfg.INITIAL_CAPITAL, total_cash)
                profit_remainder = total_cash - secure_amount

                self.vault.deposit(secure_amount, self.active_bot.bot_id, self.generation)

                if profit_remainder < 0.50:
                    logger.warning(
                        f"⚠️  Profit remainder (${profit_remainder:.2f}) is too low. "
                        f"Re-initializing with minimum viable capital."
                    )
                    profit_remainder = max(profit_remainder, 0.50)

                # Respawn with only the profit
                mutated_params = self.active_bot.params.mutate(rate=cfg.MUTATION_RATE * 0.5)  # Less mutation on success
                self.active_capital = profit_remainder
                self._spawn_bot(mutated_params, self.active_capital, ticker)

        # Final report
        self._print_final_report(ticker)

    def _spawn_bot(self, params: StrategyParams, capital: float, ticker: str) -> None:
        """Creates and starts a new TradingBot."""
        self.generation += 1
        self.total_bots_spawned += 1
        self.active_bot = TradingBot(
            generation=self.generation,
            params=params,
            initial_capital=capital,
            ticker=ticker,
        )
        self.active_bot.start()

    def _print_final_report(self, ticker: str) -> None:
        """Prints the final summary of the evolutionary run."""
        logger.info("\n" + "=" * 70)
        logger.info("📋 EVOLUTIONARY TRADING SYSTEM - FINAL REPORT")
        logger.info("=" * 70)
        logger.info(f"  Ticker Traded: {ticker}")
        logger.info(f"  Total Generations: {self.generation}")
        logger.info(f"  Bots Spawned: {self.total_bots_spawned}")
        logger.info(f"  Bots Killed (Drawdown): {self.total_bots_killed}")
        logger.info(f"  Bots That Secured Capital: {self.total_bots_secured}")
        logger.info(f"  Active Bot Remaining Capital: ${self.active_capital:.4f}")
        logger.info("-" * 70)
        logger.info(f"  🔒 Vault Balance (Secured Capital): ${self.vault.balance:.2f}")
        logger.info(f"  📊 Total System Value: ${self.vault.balance + self.active_capital:.2f}")
        logger.info(f"  💵 Initial Investment: ${cfg.INITIAL_CAPITAL:.2f}")
        total_return = ((self.vault.balance + self.active_capital) / cfg.INITIAL_CAPITAL - 1) * 100
        logger.info(f"  📈 Total Return: {total_return:+.2f}%")
        logger.info("-" * 70)

        if self.vault.total_deposits > 0:
            logger.info("\n" + self.vault.get_ledger_report())

        # Print top bot performances
        if self.bot_history:
            logger.info("\n--- Generation Performance Log ---")
            for bot in self.bot_history:
                status = "🟢 SECURED" if bot.state == BotState.CAPITAL_SECURED else "🔴 KILLED"
                logger.info(
                    f"  Gen {bot.generation:>3} | Bot#{bot.bot_id} | {status} | "
                    f"Bars: {bot.bars_processed:>4} | Final Cash: ${bot.get_remaining_capital():.4f}"
                )

        logger.info("=" * 70)
