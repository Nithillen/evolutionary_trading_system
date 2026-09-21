"""
Safe Vault Module
=================
An isolated, append-only ledger for secured capital.
Once capital is moved into the Vault, it is permanently protected
from any active trading bot. Implements the "House Money" rule.
"""

import logging
from dataclasses import dataclass, field
from typing import List
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class VaultTransaction:
    """Immutable record of a single vault deposit."""

    timestamp: str
    amount: float
    source_bot_id: str
    generation: int

    def __str__(self) -> str:
        return f"[{self.timestamp}] +${self.amount:.2f} from Bot#{self.source_bot_id} (Gen {self.generation})"


class SafeVault:
    """
    Append-only capital vault. Represents the "house money" that has been
    permanently secured from trading risk.

    Key invariant: balance can only increase. There is no withdraw method.
    """

    def __init__(self):
        self._balance: float = 0.0
        self._ledger: List[VaultTransaction] = []

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def total_deposits(self) -> int:
        return len(self._ledger)

    def deposit(self, amount: float, bot_id: str, generation: int) -> None:
        """
        Deposits secured capital into the vault.

        Args:
            amount: The dollar amount to secure.
            bot_id: The identifier of the bot that generated this profit.
            generation: The evolutionary generation number.
        """
        if amount <= 0:
            logger.warning(f"Attempted to deposit non-positive amount: ${amount:.2f}. Ignoring.")
            return

        txn = VaultTransaction(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            amount=amount,
            source_bot_id=bot_id,
            generation=generation,
        )
        self._balance += amount
        self._ledger.append(txn)

        logger.info(
            f"💰 [CAPITAL SECURED] ${amount:.2f} deposited to Vault by Bot#{bot_id}. "
            f"Vault Balance: ${self._balance:.2f}"
        )

    def get_ledger_report(self) -> str:
        """Returns a formatted string of all vault transactions."""
        if not self._ledger:
            return "Vault is empty. No capital has been secured yet."

        lines = ["=" * 60, "SAFE VAULT LEDGER", "=" * 60]
        for txn in self._ledger:
            lines.append(str(txn))
        lines.append("-" * 60)
        lines.append(f"TOTAL SECURED: ${self._balance:.2f}")
        lines.append(f"TOTAL DEPOSITS: {len(self._ledger)}")
        lines.append("=" * 60)
        return "\n".join(lines)
