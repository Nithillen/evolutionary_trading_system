"""
Configuration Module
====================
Centralized configuration for the Evolutionary Trading System.
All tunable hyperparameters, API keys, and system constants are defined here.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class SystemConfig:
    """Immutable system-wide configuration."""

    # --- Capital Management ---
    INITIAL_CAPITAL: float = 5.00
    KILL_THRESHOLD: float = 4.00
    PROFIT_TARGET: float = 7.00
    TRANSACTION_FEE_PCT: float = 0.001  # 0.1% per trade (simulated slippage + fees)

    # --- Evolutionary Engine ---
    MAX_GENERATIONS: int = 50
    MAX_BOTS_PER_GENERATION: int = 1  # Sequential evolution (one bot at a time)
    MUTATION_RATE: float = 0.3  # How much parameters change on mutation
    EVALUATION_WINDOW_BARS: int = 200  # Number of bars to evaluate a bot before forcing a decision

    # --- Market Data ---
    DEFAULT_TICKERS: List[str] = field(default_factory=lambda: ["AAPL", "MSFT", "GOOGL", "AMZN", "META"])
    DEFAULT_INTERVAL: str = "1h"
    DEFAULT_LOOKBACK_PERIOD: str = "60d"

    # --- Strategy Parameter Bounds ---
    SMA_FAST_RANGE: tuple = (5, 30)
    SMA_SLOW_RANGE: tuple = (30, 100)
    RSI_PERIOD_RANGE: tuple = (7, 28)
    RSI_OVERSOLD_RANGE: tuple = (20, 40)
    RSI_OVERBOUGHT_RANGE: tuple = (60, 80)
    MOMENTUM_LOOKBACK_RANGE: tuple = (5, 30)

    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
