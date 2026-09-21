# 🧬 Evolutionary Autonomous Trading System

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Architecture](https://img.shields.io/badge/Architecture-OOP-blueviolet)
![Async](https://img.shields.io/badge/Async-asyncio-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Paper%20Trading-orange)

An autonomous trading system inspired by **evolutionary algorithms**. Trading bots are spawned with randomized strategy parameters, evaluated against live market data, and either **killed** (if they underperform) or **rewarded** (if they hit profit targets). Killed bots mutate their DNA and respawn as improved successors. Profitable bots lock in the initial capital to an untouchable **Safe Vault** and continue trading exclusively with generated profits — the **"House Money" rule**.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     EVOLUTIONARY ENGINE                         │
│                                                                 │
│   ┌──────────┐     ┌────────────┐     ┌──────────────────┐     │
│   │  Market   │────▶│  Trading   │────▶│    Portfolio      │     │
│   │ DataFeed  │     │    Bot     │     │    Manager        │     │
│   └──────────┘     └─────┬──────┘     └──────────────────┘     │
│                          │                                      │
│              ┌───────────┼───────────┐                          │
│              ▼                       ▼                          │
│     ┌────────────────┐     ┌─────────────────┐                  │
│     │  💀 KILL SWITCH │     │ 🔒 SECURE CAPITAL│                  │
│     │  (Drawdown)     │     │ (Profit Target)  │                  │
│     └───────┬────────┘     └────────┬────────┘                  │
│             │                       │                           │
│             ▼                       ▼                           │
│     ┌──────────────┐       ┌──────────────┐                    │
│     │   MUTATE &    │       │  SAFE VAULT   │                    │
│     │   RESPAWN     │       │  (Locked $$$)  │                    │
│     └──────────────┘       └──────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Core Concepts

### The Evolutionary Lifecycle

| Phase | Description |
|-------|-------------|
| **🤖 Spawn** | A new `TradingBot` is created with randomized strategy parameters (SMA windows, RSI thresholds, momentum periods). |
| **💵 Fund** | The bot is allocated initial capital (default: \$5.00). |
| **📊 Trade** | The bot processes market data bar-by-bar, generating BUY/SELL/HOLD signals via its composite strategy. |
| **💀 Kill Switch** | If portfolio value drops below a threshold (default: \$4.00), the bot is immediately terminated. Its parameters are **mutated** and a successor is spawned with the remaining capital. |
| **🔒 Capital Secured** | If portfolio value reaches the profit target (default: \$7.00), the initial investment (\$5.00) is moved to the **Safe Vault**. The bot respawns with only the \$2.00 profit. |

### The "House Money" Rule

> Once initial capital is secured, the active bot can only ever risk **generated profit**. The principal is permanently locked in an append-only vault — even a catastrophic failure cannot touch it.

### Strategy: SMA + RSI + Momentum Composite

The strategy combines three independent indicators into a high-conviction signal:

- **Dual SMA Crossover** — Identifies the prevailing trend direction.
- **RSI Filter** — Confirms mean-reversion entry conditions (oversold/overbought zones).
- **Price Momentum** — Validates that short-term momentum aligns with the trade direction.

A signal is only generated when **all three indicators agree**, reducing false positives.

---

## 📁 Project Structure

```text
evolutionary_trading_system/
├── main.py                 # Async entry point
├── config.py               # Centralized configuration (frozen dataclass)
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT License
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── engine.py           # Evolutionary Engine (master orchestrator)
│   ├── bot.py              # TradingBot class (autonomous agent)
│   ├── portfolio.py        # PortfolioManager (paper trading, PnL tracking)
│   ├── strategies.py       # Parameterized strategies with mutation support
│   ├── data_feed.py        # Async market data feed (yfinance)
│   └── vault.py            # Append-only Safe Vault (capital preservation)
└── README.md
```

---

## 🛠️ Technical Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Market Data | `yfinance` (swappable with `ccxt` for crypto or `alpaca-trade-api`) |
| Async Runtime | `asyncio` (non-blocking data fetch and trade execution) |
| Architecture | Object-Oriented Programming with Abstract Base Classes |
| Configuration | Immutable `@dataclass(frozen=True)` |
| Logging | Python `logging` module with structured event tags |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Internet connection (for fetching market data)

### Installation

```bash
git clone https://github.com/Nithillen/evolutionary_trading_system.git
cd evolutionary_trading_system
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

The system will:
1. Randomly select a ticker from the S&P 500 tech basket.
2. Spawn a bot with randomized strategy parameters.
3. Stream historical data bar-by-bar to simulate live trading.
4. Print structured logs for every lifecycle event.

### Sample Output

```
2024-01-15 10:00:01 | INFO     | main                 | Selected ticker for this run: AAPL
2024-01-15 10:00:02 | INFO     | src.bot              | 🤖 [BOT SPAWNED] Bot#a3f1c2d9 | Gen 1 | Capital: $5.00
2024-01-15 10:00:03 | INFO     | src.portfolio        | 📈 [TRADE EXECUTED] BUY 0.027 AAPL @ $185.20
2024-01-15 10:00:05 | WARNING  | src.bot              | 💀 [BOT KILLED - DRAWDOWN REACHED] Bot#a3f1c2d9
2024-01-15 10:00:05 | INFO     | src.bot              | 🤖 [BOT SPAWNED] Bot#b7e4d1f0 | Gen 2 | Capital: $4.12
2024-01-15 10:00:08 | INFO     | src.bot              | 🔒 [CAPITAL SECURED - TRADING WITH PROFITS] Bot#b7e4d1f0
2024-01-15 10:00:08 | INFO     | src.vault            | 💰 [CAPITAL SECURED] $5.00 deposited to Vault
```

---

## ⚙️ Configuration

All hyperparameters are tunable via [`config.py`](config.py):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `INITIAL_CAPITAL` | \$5.00 | Starting capital per bot |
| `KILL_THRESHOLD` | \$4.00 | Portfolio value that triggers bot termination |
| `PROFIT_TARGET` | \$7.00 | Portfolio value that triggers capital lock-in |
| `MUTATION_RATE` | 0.30 | Probability of each parameter being re-randomized |
| `MAX_GENERATIONS` | 50 | Maximum number of evolutionary generations |
| `TRANSACTION_FEE_PCT` | 0.1% | Simulated transaction cost per trade |

---

## 🔬 Design Decisions

- **No Look-Ahead Bias:** Strategies only access historical data up to the current bar via `get_historical_window()`. Future bars are never visible to the bot.
- **Append-Only Vault:** The `SafeVault` class has no `withdraw()` method by design — capital, once secured, is permanently protected.
- **Frozen Configuration:** `SystemConfig` is an immutable `@dataclass(frozen=True)`, preventing runtime mutation of global parameters.
- **Async-First:** The data feed uses `asyncio` and `run_in_executor` to avoid blocking the event loop during network calls.

---

## 📈 Author

**Nithillen**
*Quantitative Developer | Machine Learning Engineer | Statistical Modeling*

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

> ⚠️ **Disclaimer:** This project is for educational and research purposes only. It does not constitute financial advice. Always perform your own due diligence before trading with real capital.
