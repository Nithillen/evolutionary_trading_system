"""
Trading Strategies Module
=========================
Defines modular, parameterized trading strategies that can be randomized and mutated
by the Evolutionary Engine. Each strategy consumes a historical window and emits a
trading signal: BUY (+1), SELL (-1), or HOLD (0).
"""

import random
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from config import SystemConfig

logger = logging.getLogger(__name__)
cfg = SystemConfig()


@dataclass
class StrategyParams:
    """Mutable container for all strategy hyperparameters."""

    sma_fast: int = 10
    sma_slow: int = 50
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    momentum_lookback: int = 10

    @classmethod
    def random(cls) -> "StrategyParams":
        """Generates a random set of strategy parameters within configured bounds."""
        return cls(
            sma_fast=random.randint(*cfg.SMA_FAST_RANGE),
            sma_slow=random.randint(*cfg.SMA_SLOW_RANGE),
            rsi_period=random.randint(*cfg.RSI_PERIOD_RANGE),
            rsi_oversold=round(random.uniform(*cfg.RSI_OVERSOLD_RANGE), 1),
            rsi_overbought=round(random.uniform(*cfg.RSI_OVERBOUGHT_RANGE), 1),
            momentum_lookback=random.randint(*cfg.MOMENTUM_LOOKBACK_RANGE),
        )

    def mutate(self, rate: float = 0.3) -> "StrategyParams":
        """
        Creates a new StrategyParams by mutating the current one.
        Each parameter has a `rate` probability of being re-randomized.
        """
        def _maybe_mutate(current, bounds):
            if random.random() < rate:
                if isinstance(current, int):
                    return random.randint(*bounds)
                return round(random.uniform(*bounds), 1)
            return current

        return StrategyParams(
            sma_fast=_maybe_mutate(self.sma_fast, cfg.SMA_FAST_RANGE),
            sma_slow=_maybe_mutate(self.sma_slow, cfg.SMA_SLOW_RANGE),
            rsi_period=_maybe_mutate(self.rsi_period, cfg.RSI_PERIOD_RANGE),
            rsi_oversold=_maybe_mutate(self.rsi_oversold, cfg.RSI_OVERSOLD_RANGE),
            rsi_overbought=_maybe_mutate(self.rsi_overbought, cfg.RSI_OVERBOUGHT_RANGE),
            momentum_lookback=_maybe_mutate(self.momentum_lookback, cfg.MOMENTUM_LOOKBACK_RANGE),
        )

    def to_dict(self) -> dict:
        return {
            "sma_fast": self.sma_fast,
            "sma_slow": self.sma_slow,
            "rsi_period": self.rsi_period,
            "rsi_oversold": self.rsi_oversold,
            "rsi_overbought": self.rsi_overbought,
            "momentum_lookback": self.momentum_lookback,
        }


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies."""

    def __init__(self, params: StrategyParams):
        self.params = params

    @abstractmethod
    def generate_signal(self, historical_data: pd.DataFrame) -> int:
        """
        Generates a trading signal based on historical data.

        Args:
            historical_data: DataFrame with columns like 'close', 'high', 'low', 'volume'.

        Returns:
            +1 for BUY, -1 for SELL, 0 for HOLD.
        """
        ...


class SMAMomentumStrategy(BaseStrategy):
    """
    Composite strategy combining:
    1. Dual SMA crossover (trend following)
    2. RSI (mean reversion filter)
    3. Price momentum (confirmation)

    A BUY signal requires the fast SMA to be above the slow SMA, RSI to be in the oversold zone,
    and positive short-term momentum. A SELL signal requires the inverse conditions.
    """

    def generate_signal(self, historical_data: pd.DataFrame) -> int:
        if historical_data is None or len(historical_data) < self.params.sma_slow:
            return 0  # Not enough data

        close = historical_data["close"]

        # --- SMA Crossover ---
        sma_fast = close.rolling(window=self.params.sma_fast).mean().iloc[-1]
        sma_slow = close.rolling(window=self.params.sma_slow).mean().iloc[-1]

        # --- RSI ---
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0).rolling(window=self.params.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=self.params.rsi_period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = (100 - (100 / (1 + rs))).iloc[-1]

        # --- Momentum ---
        momentum = close.pct_change(periods=self.params.momentum_lookback).iloc[-1]

        # --- Signal Logic ---
        if sma_fast > sma_slow and rsi < self.params.rsi_oversold and momentum > 0:
            return 1  # BUY

        if sma_fast < sma_slow and rsi > self.params.rsi_overbought and momentum < 0:
            return -1  # SELL

        return 0  # HOLD
