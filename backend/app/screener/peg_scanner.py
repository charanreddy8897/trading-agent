"""Power Earnings Gap (PEG) detection and persistence."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.data.fetcher import price_fetcher
from app.models.db_models import PegSetup
from app.screener.technical import BaseScreener
from app.universe.sectors import ALL_TICKERS

logger = logging.getLogger(__name__)


@dataclass
class PegCandidate:
    """A detected PEG event before it is written to the DB."""

    peg_date: date
    peg_low: float
    gap_pct: float
    volume_multiple: float


class PegScanner(BaseScreener):
    """Scans price history for Power Earnings Gap setups.

    A PEG is defined as a gap-up ≥ *gap_min_pct* on volume ≥ *vol_multiple* × 20-day average.
    """

    def __init__(
        self,
        gap_min_pct: float = settings.peg_gap_min_pct,
        vol_multiple: float = settings.peg_volume_multiple,
    ) -> None:
        self.gap_min_pct = gap_min_pct
        self.vol_multiple = vol_multiple

    @classmethod
    def from_settings(cls) -> "PegScanner":
        return cls(
            gap_min_pct=settings.peg_gap_min_pct,
            vol_multiple=settings.peg_volume_multiple,
        )

    # ── public interface ──────────────────────────────────────────────────────

    def detect_pegs(self, df: pd.DataFrame) -> list[PegCandidate]:
        """Return a list of PEG candidates found in *df*."""
        if df.empty or len(df) < 25:
            return []

        avg_vol = df["volume"].rolling(20).mean()
        pegs: list[PegCandidate] = []

        for i in range(20, len(df)):
            today      = df.iloc[i]
            prev_close = df["close"].iloc[i - 1]
            gap_pct    = ((today["open"] - prev_close) / prev_close) * 100

            if gap_pct < self.gap_min_pct:
                continue
            vol_mult = today["volume"] / avg_vol.iloc[i]
            if vol_mult < self.vol_multiple:
                continue

            pegs.append(PegCandidate(
                peg_date=df.index[i].date(),
                peg_low=round(float(today["low"]), 4),
                gap_pct=round(float(gap_pct), 4),
                volume_multiple=round(float(vol_mult), 4),
            ))

        return pegs

    def upsert_pegs(
        self, db: Session, ticker: str, pegs: list[PegCandidate], df: pd.DataFrame
    ) -> int:
        """Persist new PEG candidates; update gap-filled status on existing ones."""
        count = 0
        for peg in pegs:
            existing = (
                db.query(PegSetup)
                .filter(PegSetup.ticker == ticker, PegSetup.peg_date == peg.peg_date)
                .first()
            )
            filled = self.check_gap_filled(df, peg.peg_date, peg.peg_low)
            if existing:
                if filled != existing.gap_filled:
                    existing.gap_filled = filled
                    db.commit()
                continue

            db.add(PegSetup(
                ticker=ticker,
                peg_date=peg.peg_date,
                peg_low=peg.peg_low,
                gap_pct=peg.gap_pct,
                volume_multiple=peg.volume_multiple,
                gap_filled=filled,
            ))
            count += 1

        db.commit()
        return count

    def get_active_pegs(self, db: Session) -> list[PegSetup]:
        return db.query(PegSetup).filter(PegSetup.gap_filled == False).all()  # noqa: E712

    def run_all(self, db: Session) -> dict[str, str]:
        results: dict[str, str] = {}
        for ticker in ALL_TICKERS:
            df   = price_fetcher.get_price_df(db, ticker)
            pegs = self.detect_pegs(df)
            new  = self.upsert_pegs(db, ticker, pegs, df)
            results[ticker] = f"{len(pegs)} detected, {new} new"
            self._log_result(ticker, results[ticker])
        return results

    # ── static helpers ────────────────────────────────────────────────────────

    @staticmethod
    def check_gap_filled(df: pd.DataFrame, peg_date: date, peg_low: float) -> bool:
        """Return True if price has traded below *peg_low* after *peg_date*."""
        after_peg = df[df.index.date > peg_date]
        if after_peg.empty:
            return False
        return bool((after_peg["low"] < peg_low).any())


peg_scanner = PegScanner.from_settings()
