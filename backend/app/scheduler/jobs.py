"""APScheduler-based job runner with a deque-backed run history."""
from __future__ import annotations

import logging
from collections import deque
from datetime import datetime
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import SessionLocal
from app.core.exceptions import TradingAgentError

logger = logging.getLogger(__name__)


class TradingScheduler:
    """Orchestrates all recurring data/analysis jobs.

    Keeps a bounded deque of recent run timestamps so the pipeline-status
    endpoint can report job history without touching the DB.

    Uses *args/**kwargs in the internal job-wrapping helper so callers
    never need to worry about session management.
    """

    _MAX_HISTORY = 50

    def __init__(self, timezone: str = "America/Los_Angeles") -> None:
        self._scheduler   = BackgroundScheduler(timezone=timezone)
        self._run_history: deque[tuple[str, datetime]] = deque(maxlen=self._MAX_HISTORY)

    # ── public interface ──────────────────────────────────────────────────────

    def start(self) -> None:
        self._add("morning_pipeline",  self._morning_pipeline,
                  CronTrigger(hour=7,      minute=0,    day_of_week="mon-fri"))
        self._add("intraday_check",    self._intraday_check,
                  CronTrigger(hour="6-13", minute="*/15", day_of_week="mon-fri"))
        self._add("evening_update",    self._evening_update,
                  CronTrigger(hour=17,     minute=0,    day_of_week="mon-fri"))
        self._scheduler.start()
        logger.info("TradingScheduler started — 3 jobs registered")

    def stop(self) -> None:
        self._scheduler.shutdown()
        logger.info("TradingScheduler stopped")

    def last_run(self, job_id: str) -> datetime | None:
        """Return the most recent run timestamp for *job_id*, or None."""
        for jid, ts in reversed(self._run_history):
            if jid == job_id:
                return ts
        return None

    # ── job implementations (called with an open DB session) ─────────────────

    def _morning_pipeline(self, db) -> None:
        from app.alerts.daily_briefing    import daily_briefing
        from app.analysis.claude_analyzer import claude_analyzer
        from app.analysis.stage_analyzer  import stage_analyzer
        from app.data.fetcher             import price_fetcher
        from app.data.news_fetcher        import news_fetcher
        from app.portfolio.alpaca_sync    import alpaca_sync
        from app.risk.stop_manager        import stop_manager
        from app.screener.base_detector   import base_detector
        from app.screener.peg_scanner     import peg_scanner
        from app.screener.technical       import technical_analyzer

        alpaca_sync.sync_positions(db)
        price_fetcher.update_all_prices(db)
        news_fetcher.update_all_news(db)
        technical_analyzer.run_all(db)
        peg_scanner.run_all(db)
        base_detector.run_all(db)
        stage_analyzer.run_all(db)
        claude_analyzer.run_all(db)

        signals = stop_manager.check_sell_signals(db)
        stop_manager.save_alerts(db, signals)
        daily_briefing.send_briefing(db)

    def _intraday_check(self, db) -> None:
        from app.alerts.notifier   import slack_notifier
        from app.risk.stop_manager import stop_manager

        signals = stop_manager.check_sell_signals(db)
        stop_manager.save_alerts(db, signals)
        for s in signals:
            if s.severity.value == "critical":
                slack_notifier.send_alert(s.ticker, s.message, s.severity.value)

    def _evening_update(self, db) -> None:
        from app.data.fetcher      import price_fetcher
        from app.portfolio.tracker import portfolio_tracker

        price_fetcher.update_all_prices(db)
        summary = portfolio_tracker.get_summary(db)
        logger.info("Evening update: portfolio $%.2f", summary["total_value"])

    # ── private helpers ───────────────────────────────────────────────────────

    def _add(self, job_id: str, fn: Callable, trigger) -> None:
        """Register a job with automatic session handling and error isolation."""

        def _wrapped(*args, **kwargs):
            logger.info("=== %s START ===", job_id.upper())
            db = SessionLocal()
            try:
                fn(db, *args, **kwargs)
                self._record(job_id)
                logger.info("=== %s COMPLETE ===", job_id.upper())
            except TradingAgentError as exc:
                logger.error("%s domain error: %s", job_id, exc)
            except Exception as exc:  # noqa: BLE001
                logger.error("%s unexpected error: %s", job_id, exc)
            finally:
                db.close()

        self._scheduler.add_job(_wrapped, trigger, id=job_id)

    def _record(self, job_id: str) -> None:
        self._run_history.append((job_id, datetime.now()))


trading_scheduler = TradingScheduler()
