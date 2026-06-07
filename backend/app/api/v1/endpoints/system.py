"""System health and manual pipeline trigger endpoints."""
from __future__ import annotations

import logging
import threading
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.database import check_db, get_db
from app.core.exceptions import TradingAgentError
from app.schemas.responses import HealthSchema, PipelineStatusSchema

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Thread-safe pipeline state (replaces bare module-level globals) ───────────
_lock             = threading.Lock()
_pipeline_running = False
_last_run: str | None = None


@router.get("/health", response_model=HealthSchema)
async def health_check(db: Session = Depends(get_db)):
    return HealthSchema(status="ok", db="ok" if check_db() else "error")


@router.post("/run-pipeline", response_model=PipelineStatusSchema)
async def run_pipeline(background: BackgroundTasks, db: Session = Depends(get_db)):
    global _pipeline_running
    with _lock:
        if _pipeline_running:
            return PipelineStatusSchema(
                running=True, last_run=_last_run, message="Pipeline already running"
            )
        _pipeline_running = True

    background.add_task(_execute_pipeline)
    return PipelineStatusSchema(running=True, last_run=_last_run, message="Pipeline started")


@router.get("/pipeline-status", response_model=PipelineStatusSchema)
async def pipeline_status():
    with _lock:
        running  = _pipeline_running
        last_run = _last_run
    return PipelineStatusSchema(
        running=running,
        last_run=last_run,
        message="Running" if running else "Idle",
    )


def _execute_pipeline() -> None:
    global _pipeline_running, _last_run
    try:
        from app.core.database    import SessionLocal
        from app.analysis.stage_analyzer import stage_analyzer
        from app.data.fetcher     import price_fetcher
        from app.data.news_fetcher import news_fetcher
        from app.screener.base_detector import base_detector
        from app.screener.peg_scanner   import peg_scanner
        from app.screener.technical     import technical_analyzer

        db = SessionLocal()
        try:
            logger.info("Manual pipeline: prices")
            price_fetcher.update_all_prices(db)
            logger.info("Manual pipeline: news")
            news_fetcher.update_all_news(db)
            logger.info("Manual pipeline: technicals")
            technical_analyzer.run_all(db)
            logger.info("Manual pipeline: PEGs")
            peg_scanner.run_all(db)
            logger.info("Manual pipeline: base numbers")
            base_detector.run_all(db)
            logger.info("Manual pipeline: Weinstein stages")
            stage_analyzer.run_all(db)
            with _lock:
                _last_run = datetime.now().isoformat()
            logger.info("Manual pipeline complete")
        finally:
            db.close()
    except TradingAgentError as exc:
        logger.error("Pipeline domain error: %s", exc)
    except Exception as exc:  # noqa: BLE001
        logger.error("Pipeline unexpected error: %s", type(exc).__name__)
    finally:
        with _lock:
            _pipeline_running = False
