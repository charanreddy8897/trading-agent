"""Daily trading briefing — assembles a rich Slack summary every morning."""
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import date

from sqlalchemy.orm import Session

from app.alerts.notifier import SlackNotifier, slack_notifier
from app.analysis.scoring import UniverseScorer, universe_scorer
from app.models.db_models import NewsItem
from app.portfolio.tracker import PortfolioTracker, portfolio_tracker
from app.risk.exposure import ExposureCalculator, exposure_calculator
from app.risk.stop_manager import SellSignal, StopManager, stop_manager
from app.screener.peg_scanner import PegScanner, peg_scanner
from app.universe.sectors import SECTORS

logger = logging.getLogger(__name__)


class DailyBriefing:
    """Assembles and sends the morning trading briefing to Slack.

    Dependencies are injected so the class is independently testable.
    """

    MIN_SCORE_THRESHOLD = 60

    def __init__(
        self,
        notifier: SlackNotifier,
        scorer: UniverseScorer,
        tracker: PortfolioTracker,
        exposure_calc: ExposureCalculator,
        stop_mgr: StopManager,
        peg_scan: PegScanner,
    ) -> None:
        self._notifier     = notifier
        self._scorer       = scorer
        self._tracker      = tracker
        self._exposure     = exposure_calc
        self._stop_mgr     = stop_mgr
        self._peg_scanner  = peg_scan

    @classmethod
    def from_singletons(cls) -> "DailyBriefing":
        return cls(
            notifier=slack_notifier,
            scorer=universe_scorer,
            tracker=portfolio_tracker,
            exposure_calc=exposure_calculator,
            stop_mgr=stop_manager,
            peg_scan=peg_scanner,
        )

    # ── public interface ──────────────────────────────────────────────────────

    def generate(self, db: Session) -> str:
        """Build the full briefing text from current DB state."""
        today    = date.today().strftime("%A, %B %d, %Y")
        summary  = self._tracker.get_summary(db)
        exposure = self._exposure.calc_exposure(db)
        signals  = self._stop_mgr.check_sell_signals(db)
        ranking  = self._scorer.rank_universe(db)
        top10    = [r for r in ranking.rows if r.total >= self.MIN_SCORE_THRESHOLD][:10]
        pegs     = self._peg_scanner.get_active_pegs(db)
        leaders  = self._scorer.sector_leaders(db)

        severity_count: Counter[str] = Counter(s.severity.value for s in signals)
        sector_news: defaultdict[str, list[str]] = defaultdict(list)
        for sector, tickers in SECTORS.items():
            rows = (
                db.query(NewsItem)
                .filter(NewsItem.ticker.in_(tickers))
                .order_by(NewsItem.published_at.desc())
                .limit(3)
                .all()
            )
            for n in rows:
                sector_news[sector].append(n.headline)

        lines: list[str] = [
            f"*📊 DAILY TRADING BRIEFING — {today}*", "",
            "*1. YOUR PORTFOLIO*",
            f"  Total Value:    ${summary['total_value']:,.2f}",
            f"  Unrealised P&L: ${summary['total_pnl']:,.2f}",
            f"  Open Positions: {summary['position_count']}",
            "",
        ]

        if exposure.warnings:
            lines.append("*⚠️ EXPOSURE WARNINGS*")
            lines += [f"  • {w}" for w in exposure.warnings]
            lines.append("")

        if signals:
            critical = severity_count.get("critical", 0)
            lines.append(f"*🚨 SELL SIGNALS* ({critical} critical, {len(signals)} total)")
            lines += [f"  • [{s.severity.value.upper()}] {s.message}" for s in signals]
            lines.append("")

        lines.append("*2. TOP SETUPS (score ≥ 60)*")
        for r in top10:
            peg_tag = " ⚡PEG" if r.peg_active else ""
            lines.append(
                f"  {r.ticker:6s} | Score:{r.total:3d} | "
                f"Stage:{r.stage} | ADR:{r.adr_pct}%{peg_tag}"
            )
        lines.append("")

        lines.append("*3. ACTIVE PEG SETUPS*")
        if pegs:
            lines += [f"  ⚡ {p.ticker} | Gap:{p.gap_pct:.1f}% | PEG Low:${p.peg_low}" for p in pegs]
        else:
            lines.append("  No active PEGs")
        lines.append("")

        top_sector = leaders[0].sector if leaders else "N/A"
        lines.append(f"*4. SECTOR LEADERSHIP*  → {top_sector}")
        for lead in leaders:
            lines.append(f"  {lead.sector:25s} avg score: {lead.avg_score}")
        lines.append("")

        if sector_news:
            lines.append("*5. SECTOR NEWS*")
            for sector, headlines in sector_news.items():
                lines.append(f"  *{sector}*")
                lines += [f"    • {h[:100]}" for h in headlines]
            lines.append("")

        return "\n".join(lines)

    def send_briefing(self, db: Session) -> bool:
        """Generate and deliver the briefing to the Slack briefing channel."""
        try:
            text = self.generate(db)
            ok   = self._notifier.send("briefing", text)
            logger.info("Daily briefing sent: %s", ok)
            return ok
        except Exception as exc:
            logger.error("Briefing generation failed: %s", exc)
            return False


daily_briefing = DailyBriefing.from_singletons()
