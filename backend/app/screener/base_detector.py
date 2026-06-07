"""O'Neil base-count detection — counts consolidation periods in an uptrend."""
from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy.orm import Session

from app.data.fetcher import price_fetcher
from app.models.db_models import TechnicalSignal
from app.screener.technical import BaseScreener
from app.universe.sectors import ALL_TICKERS

logger = logging.getLogger(__name__)


class BaseDetector(BaseScreener):
    """Counts O'Neil consolidation bases (consolidations < 30% over 6+ weeks).

    A higher base count means the stock is further into its run (riskier).
    """

    BASE_RANGE_PCT  = 30.0
    MIN_BASE_WEEKS  = 6
    MAX_BASE_REPORT = 4

    def __init__(self, range_pct: float = BASE_RANGE_PCT, min_weeks: int = MIN_BASE_WEEKS) -> None:
        self.range_pct = range_pct
        self.min_weeks = min_weeks

    # ── public interface ──────────────────────────────────────────────────────

    def detect_base_number(self, df: pd.DataFrame) -> int:
        """Count valid bases in *df*; returns 0 if insufficient history."""
        if df.empty or len(df) < 60:
            return 0

        weekly = df["close"].resample("W").last().dropna()
        if len(weekly) < 12:
            return 0

        return min(self._count_bases(weekly), self.MAX_BASE_REPORT)

    def update_base_numbers(self, db: Session) -> dict[str, int]:
        """Recompute and persist base numbers for the full universe."""
        results: dict[str, int] = {}
        for ticker in ALL_TICKERS:
            df = price_fetcher.get_price_df(db, ticker)
            if df.empty:
                continue
            base_num = self.detect_base_number(df)
            self._write_base_number(db, ticker, base_num)
            results[ticker] = base_num
            self._log_result(ticker, str(base_num))
        return results

    def run_all(self, db: Session) -> dict[str, str]:
        return {t: str(v) for t, v in self.update_base_numbers(db).items()}

    # ── private helpers ───────────────────────────────────────────────────────

    def _count_bases(self, weekly: pd.Series) -> int:
        base_count = 0
        in_base    = False
        base_start = 0

        for i in range(self.min_weeks, len(weekly)):
            window  = weekly.iloc[i - self.min_weeks: i]
            high, low = window.max(), window.min()
            rng_pct   = ((high - low) / low) * 100

            if rng_pct < self.range_pct:
                if not in_base:
                    in_base    = True
                    base_start = i
            else:
                if in_base and (i - base_start) >= self.min_weeks:
                    base_count += 1
                in_base = False

        if in_base and (len(weekly) - base_start) >= self.min_weeks:
            base_count += 1

        return base_count

    @staticmethod
    def _write_base_number(db: Session, ticker: str, base_num: int) -> None:
        latest = (
            db.query(TechnicalSignal)
            .filter(TechnicalSignal.ticker == ticker)
            .order_by(TechnicalSignal.date.desc())
            .first()
        )
        if latest:
            latest.base_number = base_num
            db.commit()


base_detector = BaseDetector()
