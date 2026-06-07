"""Universe scorer — ranks every ticker with a composite technical/setup/fundamental score."""
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import NamedTuple

from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.db_models import ClaudeAnalysis, PegSetup, TechnicalSignal
from app.universe.sectors import ALL_TICKERS, TICKER_SECTOR

logger = logging.getLogger(__name__)


class SectorLeader(NamedTuple):
    """Lightweight immutable summary of a sector's average composite score."""
    sector: str
    avg_score: float
    ticker_count: int


@dataclass
class TickerScore:
    """Composite score for a single ticker."""
    ticker: str
    sector: str
    technical: int
    setup: int
    fundamental: int
    total: int
    action: str | None = None
    stage: int | None = None
    base_number: int | None = None
    adr_pct: float | None = None
    atr_extension: float | None = None
    rvol: float | None = None
    peg_active: bool = False


@dataclass
class UniverseRanking:
    """Result of a full universe ranking pass."""
    rows: list[TickerScore] = field(default_factory=list)
    stage_distribution: Counter = field(default_factory=Counter)
    action_distribution: Counter = field(default_factory=Counter)


class UniverseScorer:
    """Scores and ranks the full ticker universe using a composite signal."""

    # Score weights
    _MA_SCORE        = 5   # per moving average
    _ADR_SCORE       = 5
    _ATR_SCORE       = 5
    _RVOL_SCORE      = 5
    _STAGE2_SCORE    = 5
    _PEG_SCORE       = 15
    _EARLY_BASE_SCORE = 10
    _TIGHT_EMA_SCORE = 5
    _MAX_FUND_SCORE  = 30  # conviction/10 × 30

    def __init__(
        self,
        adr_min: float = settings.adr_min,
        adr_max: float = settings.adr_max,
        atr_threshold: float = 2.0,
        rvol_threshold: float = 1.5,
    ) -> None:
        self.adr_min       = adr_min
        self.adr_max       = adr_max
        self.atr_threshold = atr_threshold
        self.rvol_threshold = rvol_threshold

    # ── public interface ──────────────────────────────────────────────────────

    def score_ticker(self, db: Session, ticker: str) -> TickerScore:
        """Compute a composite score for a single ticker."""
        signal   = self._latest_signal(db, ticker)
        analysis = self._latest_analysis(db, ticker)
        peg      = self._active_peg(db, ticker)

        tech  = self._technical_score(signal, peg)
        setup = self._setup_score(signal, peg)
        fund  = self._fundamental_score(analysis)

        return TickerScore(
            ticker=ticker,
            sector=TICKER_SECTOR.get(ticker, "Unknown"),
            technical=tech,
            setup=setup,
            fundamental=fund,
            total=tech + setup + fund,
            action=analysis.action if analysis else None,
            stage=signal.weinstein_stage if signal else None,
            base_number=signal.base_number if signal else None,
            adr_pct=float(signal.adr_pct) if signal and signal.adr_pct else None,
            atr_extension=float(signal.atr_extension) if signal and signal.atr_extension else None,
            rvol=float(signal.rvol) if signal and signal.rvol else None,
            peg_active=peg is not None,
        )

    def rank_universe(self, db: Session) -> UniverseRanking:
        """Score every ticker, sort descending by total, build distribution counts."""
        rows = list(self._score_gen(db))
        rows.sort(key=lambda s: s.total, reverse=True)

        stage_dist: Counter[int]   = Counter(r.stage for r in rows if r.stage is not None)
        action_dist: Counter[str]  = Counter(r.action for r in rows if r.action is not None)

        return UniverseRanking(
            rows=rows,
            stage_distribution=stage_dist,
            action_distribution=action_dist,
        )

    def sector_leaders(self, db: Session) -> list[SectorLeader]:
        """Return sector leadership sorted by average composite score."""
        ranking = self.rank_universe(db)

        sector_totals: defaultdict[str, list[int]] = defaultdict(list)
        for row in ranking.rows:
            sector_totals[row.sector].append(row.total)

        leaders = [
            SectorLeader(
                sector=sector,
                avg_score=round(sum(scores) / len(scores), 1),
                ticker_count=len(scores),
            )
            for sector, scores in sector_totals.items()
        ]
        return sorted(leaders, key=lambda l: l.avg_score, reverse=True)

    # ── private helpers ───────────────────────────────────────────────────────

    def _score_gen(self, db: Session):
        """Generator that yields a TickerScore for each ticker in the universe."""
        for ticker in ALL_TICKERS:
            yield self.score_ticker(db, ticker)

    def _technical_score(self, signal: TechnicalSignal | None, peg) -> int:
        if signal is None:
            return 0
        close = signal.sma50  # best available price proxy
        score = 0
        if signal.sma200 and close and float(close) > float(signal.sma200):
            score += self._MA_SCORE
        if signal.sma50  and close and float(close) > float(signal.sma50):
            score += self._MA_SCORE
        if signal.ema21  and close and float(close) > float(signal.ema21):
            score += self._MA_SCORE
        if signal.ema9   and close and float(close) > float(signal.ema9):
            score += self._MA_SCORE
        if signal.adr_pct and self.adr_min <= float(signal.adr_pct) <= self.adr_max:
            score += self._ADR_SCORE
        if signal.atr_extension and float(signal.atr_extension) < self.atr_threshold:
            score += self._ATR_SCORE
        if signal.rvol and float(signal.rvol) > self.rvol_threshold:
            score += self._RVOL_SCORE
        if signal.weinstein_stage == 2:
            score += self._STAGE2_SCORE
        return score

    def _setup_score(self, signal: TechnicalSignal | None, peg) -> int:
        if signal is None:
            return 0
        score = 0
        if peg:
            score += self._PEG_SCORE
        base = signal.base_number or 0
        if base in (1, 2):
            score += self._EARLY_BASE_SCORE
        if signal.ema9 and signal.ema21 and signal.sma50:
            ema_avg = (float(signal.ema9) + float(signal.ema21)) / 2
            if abs(float(signal.sma50) - ema_avg) / ema_avg < 0.05:
                score += self._TIGHT_EMA_SCORE
        return score

    def _fundamental_score(self, analysis: ClaudeAnalysis | None) -> int:
        if analysis and analysis.conviction:
            return round((analysis.conviction / 10) * self._MAX_FUND_SCORE)
        return 0

    # ── DB queries ────────────────────────────────────────────────────────────

    @staticmethod
    def _latest_signal(db: Session, ticker: str) -> TechnicalSignal | None:
        return (
            db.query(TechnicalSignal)
            .filter(TechnicalSignal.ticker == ticker)
            .order_by(TechnicalSignal.date.desc())
            .first()
        )

    @staticmethod
    def _latest_analysis(db: Session, ticker: str) -> ClaudeAnalysis | None:
        return (
            db.query(ClaudeAnalysis)
            .filter(ClaudeAnalysis.ticker == ticker)
            .order_by(ClaudeAnalysis.analyzed_at.desc())
            .first()
        )

    @staticmethod
    def _active_peg(db: Session, ticker: str):
        return (
            db.query(PegSetup)
            .filter(PegSetup.ticker == ticker, PegSetup.gap_filled == False)  # noqa: E712
            .order_by(PegSetup.peg_date.desc())
            .first()
        )


universe_scorer = UniverseScorer()
