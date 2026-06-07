"""Technical indicator computation — EMA, SMA, ADR, ATR, RVOL."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.data.fetcher import price_fetcher
from app.models.db_models import TechnicalSignal
from app.universe.sectors import ALL_TICKERS

logger = logging.getLogger(__name__)


# ── Abstract base for all screeners ──────────────────────────────────────────

class BaseScreener(ABC):
    """Every screener must be able to run over the full universe."""

    @abstractmethod
    def run_all(self, db: Session) -> dict[str, str]:
        ...

    def _log_result(self, ticker: str, status: str) -> None:
        logger.info("[%s] %s → %s", self.__class__.__name__, ticker, status)


# ── Data container ────────────────────────────────────────────────────────────

@dataclass
class SignalSnapshot:
    """All technical indicators for a single ticker on a single date."""

    date: date
    ema9: float
    ema21: float
    sma50: float
    sma200: float
    ma10w: float
    ma30w: float
    adr_pct: float
    atr: float
    atr_extension: float
    rvol: float


# ── Concrete class ────────────────────────────────────────────────────────────

class TechnicalAnalyzer(BaseScreener):
    """Computes and persists technical indicators for the trading universe."""

    def __init__(self, adr_window: int = 14, atr_window: int = 14, rvol_window: int = 20) -> None:
        self.adr_window = adr_window
        self.atr_window = atr_window
        self.rvol_window = rvol_window

    # ── public interface ──────────────────────────────────────────────────────

    def compute_signals(self, df: pd.DataFrame) -> SignalSnapshot | None:
        """Compute all indicators from a price DataFrame; return None if insufficient data."""
        if df.empty or len(df) < 50:
            return None

        close  = df["close"]
        high   = df["high"]
        low    = df["low"]
        volume = df["volume"]

        ema9   = close.ewm(span=9,   adjust=False).mean()
        ema21  = close.ewm(span=21,  adjust=False).mean()
        sma50  = close.rolling(50).mean()
        sma200 = close.rolling(200).mean()
        ma10w  = close.rolling(50).mean()
        ma30w  = close.rolling(150).mean()

        daily_range_pct = ((high - low) / low) * 100
        adr = daily_range_pct.rolling(self.adr_window).mean()

        prev_close = close.shift(1)
        tr = pd.concat(
            [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
            axis=1,
        ).max(axis=1)
        atr = tr.rolling(self.atr_window).mean()

        atr_extension = (close - sma50) / atr
        avg_vol = volume.rolling(self.rvol_window).mean()
        rvol    = volume / avg_vol

        return SignalSnapshot(
            date=df.index[-1].date(),
            ema9=round(float(ema9.iloc[-1]),  4),
            ema21=round(float(ema21.iloc[-1]), 4),
            sma50=round(float(sma50.iloc[-1]), 4),
            sma200=round(float(sma200.iloc[-1]), 4) if not np.isnan(sma200.iloc[-1]) else 0.0,
            ma10w=round(float(ma10w.iloc[-1]), 4),
            ma30w=round(float(ma30w.iloc[-1]), 4),
            adr_pct=round(float(adr.iloc[-1]),   4),
            atr=round(float(atr.iloc[-1]),   4),
            atr_extension=round(float(atr_extension.iloc[-1]), 4),
            rvol=round(float(rvol.iloc[-1]),  4),
        )

    def upsert_signals(self, db: Session, ticker: str, snap: SignalSnapshot) -> None:
        """Write a SignalSnapshot to the DB; skip if the date already exists."""
        existing = (
            db.query(TechnicalSignal)
            .filter(TechnicalSignal.ticker == ticker, TechnicalSignal.date == snap.date)
            .first()
        )
        if existing:
            return
        db.add(TechnicalSignal(
            ticker=ticker,
            date=snap.date,
            ema9=snap.ema9,
            ema21=snap.ema21,
            sma50=snap.sma50,
            sma200=snap.sma200,
            ma10w=snap.ma10w,
            ma30w=snap.ma30w,
            adr_pct=snap.adr_pct,
            atr=snap.atr,
            atr_extension=snap.atr_extension,
            rvol=snap.rvol,
        ))
        db.commit()

    def run_all(self, db: Session) -> dict[str, str]:
        """Compute and persist signals for every ticker in the universe."""
        results: dict[str, str] = {}
        for ticker in ALL_TICKERS:
            df = price_fetcher.get_price_df(db, ticker)
            snap = self.compute_signals(df)
            if snap:
                self.upsert_signals(db, ticker, snap)
                results[ticker] = "ok"
                self._log_result(ticker, "ok")
            else:
                results[ticker] = "insufficient data"
                self._log_result(ticker, "insufficient data")
        return results


technical_analyzer = TechnicalAnalyzer()
