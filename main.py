"""
Main Entry Point
=================
Launches the Evolutionary Trading System.
"""

import asyncio
import logging
import random

from config import SystemConfig
from src.engine import EvolutionaryEngine

cfg = SystemConfig()


def setup_logging() -> None:
    """Configures the root logger for the entire system."""
    logging.basicConfig(
        level=getattr(logging, cfg.LOG_LEVEL),
        format=cfg.LOG_FORMAT,
        datefmt=cfg.LOG_DATE_FORMAT,
    )
    # Suppress noisy third-party loggers
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("peewee").setLevel(logging.WARNING)


async def main() -> None:
    """Async entry point for the evolutionary trading system."""
    setup_logging()
    logger = logging.getLogger("main")

    # Select a random ticker from the default list for diversity
    ticker = random.choice(cfg.DEFAULT_TICKERS)
    logger.info(f"Selected ticker for this run: {ticker}")

    # Initialize and run the evolutionary engine
    engine = EvolutionaryEngine()
    await engine.run(ticker=ticker)


if __name__ == "__main__":
    asyncio.run(main())
