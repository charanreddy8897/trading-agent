"""Alpaca portfolio sync — pulls live/paper positions into the local DB."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import SyncError
from app.core.settings import settings
from app.portfolio.tracker import portfolio_tracker

logger = logging.getLogger(__name__)


@dataclass
class AccountSnapshot:
    """Immutable summary of an Alpaca account at a point in time."""

    portfolio_value: float
    cash: float
    equity: float
    last_equity: float

    @property
    def daily_change(self) -> float:
        return self.equity - self.last_equity

    @property
    def daily_pct(self) -> float:
        return (self.daily_change / self.last_equity * 100) if self.last_equity else 0.0


class AlpacaSync:
    """Synchronises Alpaca paper/live positions and snapshots into the local DB."""

    def __init__(
        self,
        api_key: str = settings.alpaca_api_key,
        secret_key: str = settings.alpaca_secret_key,
        paper: bool = True,
    ) -> None:
        self._api_key    = api_key
        self._secret_key = secret_key
        self._paper      = paper
        self._client     = None

    @classmethod
    def from_settings(cls) -> "AlpacaSync":
        return cls(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            paper=settings.trading_mode == "paper",
        )

    # ── public interface ──────────────────────────────────────────────────────

    def sync_positions(self, db: Session) -> dict:
        """Pull positions from Alpaca and upsert them into the DB."""
        try:
            client    = self._get_client()
            positions = client.get_all_positions()
            account   = client.get_account()
            snap      = self._parse_account(account)

            for pos in positions:
                portfolio_tracker.upsert_position(
                    db=db,
                    ticker=pos.symbol,
                    shares=float(pos.qty),
                    avg_cost=float(pos.avg_entry_price),
                    current_price=float(pos.current_price),
                    entry_date=date.today(),
                )

            portfolio_tracker.snapshot_portfolio(
                db,
                total_value=snap.portfolio_value,
                cash=snap.cash,
                daily_change=snap.daily_change,
                daily_pct=snap.daily_pct,
            )

            logger.info("Alpaca sync: %d positions, portfolio $%.2f", len(positions), snap.portfolio_value)
            return {
                "positions":   len(positions),
                "total_value": snap.portfolio_value,
                "cash":        snap.cash,
            }

        except SyncError:
            raise
        except Exception as exc:
            raise SyncError(f"Alpaca sync failed: {exc}") from exc

    # ── private helpers ───────────────────────────────────────────────────────

    def _get_client(self):
        if self._client is None:
            from alpaca.trading.client import TradingClient
            self._client = TradingClient(self._api_key, self._secret_key, paper=self._paper)
        return self._client

    @staticmethod
    def _parse_account(account) -> AccountSnapshot:
        return AccountSnapshot(
            portfolio_value=float(account.portfolio_value),
            cash=float(account.cash),
            equity=float(account.equity),
            last_equity=float(account.last_equity),
        )


alpaca_sync = AlpacaSync.from_settings()
