"""
Market Data Feed Module
=======================
Handles fetching and streaming historical / real-time market data
from Yahoo Finance (yfinance). Designed to be swappable with ccxt or Alpaca.
"""

import asyncio
import logging
from typing import Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class MarketDataFeed:
    """
    Provides an async-compatible interface for streaming market data bar-by-bar.

    This class fetches a bulk historical dataset and then yields bars one at a time
    to simulate a live data stream for paper trading. This architecture cleanly
    separates data ingestion from trading logic.
    """

    def __init__(self, ticker: str, interval: str = "1h", period: str = "60d"):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self._data: Optional[pd.DataFrame] = None
        self._current_idx: int = 0

    async def initialize(self) -> None:
        """Fetches the full historical dataset asynchronously."""
        logger.info(f"Fetching market data for {self.ticker} | interval={self.interval} | period={self.period}")
        # Run the blocking yfinance call in a thread executor to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        self._data = await loop.run_in_executor(None, self._fetch_sync)

        if self._data is None or self._data.empty:
            raise ValueError(f"Failed to fetch data for {self.ticker}. Check ticker validity and network.")

        self._current_idx = 0
        logger.info(f"Loaded {len(self._data)} bars for {self.ticker}")

    def _fetch_sync(self) -> pd.DataFrame:
        """Synchronous data fetch wrapper for yfinance."""
        ticker_obj = yf.Ticker(self.ticker)
        df = ticker_obj.history(period=self.period, interval=self.interval)
        # Standardize column names to lowercase
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]
        return df

    async def get_next_bar(self) -> Optional[pd.Series]:
        """
        Yields the next bar in the dataset, simulating a live data stream.

        Returns:
            pd.Series or None if the data is exhausted.
        """
        if self._data is None:
            raise RuntimeError("DataFeed not initialized. Call initialize() first.")

        if self._current_idx >= len(self._data):
            return None  # Stream exhausted

        bar = self._data.iloc[self._current_idx]
        self._current_idx += 1
        # Simulate network latency for realism (tiny delay)
        await asyncio.sleep(0)
        return bar

    def get_historical_window(self, lookback: int) -> Optional[pd.DataFrame]:
        """
        Returns the last `lookback` bars up to (but not including) the current index.
        Used by strategies to compute indicators without look-ahead bias.
        """
        if self._data is None or self._current_idx < lookback:
            return None
        return self._data.iloc[self._current_idx - lookback : self._current_idx].copy()

    @property
    def bars_remaining(self) -> int:
        if self._data is None:
            return 0
        return len(self._data) - self._current_idx

    @property
    def total_bars(self) -> int:
        if self._data is None:
            return 0
        return len(self._data)

    def reset(self) -> None:
        """Resets the stream cursor back to the beginning."""
        self._current_idx = 0
