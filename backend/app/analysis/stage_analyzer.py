"""Weinstein Stage Analysis — classifies stocks into Stages 1-4."""
from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy.orm import Session

from app.data.fetcher import price_fetcher
from app.models.db_models import TechnicalSignal
from app.screener.technical import BaseScreener
from app.universe.sectors import ALL_TICKERS

logger = logging.getLogger(__name__)


class StageAnalyzer(BaseScreener):
    """Classifies each ticker into a Weinstein Stage using its 30-week (150-day) MA.

    Stage 1 — Basing (flat MA, price near MA)
    Stage 2 — Uptrend (rising MA, price above) — the only BUY zone
    Stage 3 — Topping (flattening MA, price oscillating)
    Stage 4 — Downtrend (declining MA, price below) — AVOID
    """

    MA_WINDOW       = 150   # 30 weeks ≈ 150 trading days
    SLOPE_LOOKBACK  = 10    # 2-week slope sample
    RISING_THRESH   = 0.5   # % slope considered "rising"
    PRICE_BUFFER    = 5.0   # % above MA still counted as Stage 1

    def __init__(
        self,
        ma_window: int = MA_WINDOW,
        slope_lookback: int = SLOPE_LOOKBACK,
        rising_thresh: float = RISING_THRESH,
    ) -> None:
        self.ma_window      = ma_window
        self.slope_lookback = slope_lookback
        self.rising_thresh  = rising_thresh

    # ── public interface ──────────────────────────────────────────────────────

    def detect_stage(self, df: pd.DataFrame) -> int:
        """Classify *df* into a Weinstein Stage (0 = insufficient data)."""
        if df.empty or len(df) < self.ma_window:
            return 0

        close = df["close"]
        ma30w = close.rolling(self.ma_window).mean()

        current_price = close.iloc[-1]
        current_ma    = ma30w.iloc[-1]
        prev_ma       = ma30w.iloc[-self.slope_lookback]

        if current_ma == 0:
            return 0

        ma_slope_pct = ((current_ma - prev_ma) / prev_ma) * 100
        price_vs_ma  = ((current_price - current_ma) / current_ma) * 100

        return self._classify(ma_slope_pct, price_vs_ma)

    def update_stages(self, db: Session) -> dict[str, int]:
        """Recompute and persist Weinstein stages for the full universe."""
        results: dict[str, int] = {}
        for ticker in ALL_TICKERS:
            df = price_fetcher.get_price_df(db, ticker)
            if df.empty:
                continue
            stage = self.detect_stage(df)
            self._write_stage(db, ticker, stage)
            results[ticker] = stage
            self._log_result(ticker, f"Stage {stage}")
        return results

    def run_all(self, db: Session) -> dict[str, str]:
        return {t: f"Stage {s}" for t, s in self.update_stages(db).items()}

    # ── private helpers ───────────────────────────────────────────────────────

    def _classify(self, ma_slope_pct: float, price_vs_ma: float) -> int:
        if ma_slope_pct > self.rising_thresh and price_vs_ma > 0:
            return 2
        if ma_slope_pct < -self.rising_thresh and price_vs_ma < 0:
            return 4
        if abs(ma_slope_pct) <= self.rising_thresh and price_vs_ma > -self.PRICE_BUFFER:
            return 1 if price_vs_ma < self.PRICE_BUFFER else 3
        return 3

    @staticmethod
    def _write_stage(db: Session, ticker: str, stage: int) -> None:
        latest = (
            db.query(TechnicalSignal)
            .filter(TechnicalSignal.ticker == ticker)
            .order_by(TechnicalSignal.date.desc())
            .first()
        )
        if latest:
            latest.weinstein_stage = stage
            db.commit()


stage_analyzer = StageAnalyzer()
