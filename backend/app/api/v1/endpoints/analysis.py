from __future__ import annotations

import re
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analysis.claude_analyzer import claude_analyzer
from app.core.database import get_db
from app.models.db_models import ClaudeAnalysis, DailyPrice, TechnicalSignal
from app.schemas.responses import AnalysisSchema
from app.universe.sectors import ALL_TICKERS

router = APIRouter()

_TICKER_RE = re.compile(r"^[A-Z]{1,10}$")


def _validate_ticker(ticker: str) -> str:
    """Normalise to uppercase and ensure it looks like a valid ticker."""
    t = ticker.strip().upper()
    if not _TICKER_RE.match(t):
        raise HTTPException(status_code=400, detail=f"Invalid ticker symbol: {ticker!r}")
    return t


def _enrich(analysis: ClaudeAnalysis, db: Session) -> dict:
    """Attach 90-day price history and latest technicals to an analysis record."""
    row = {k: v for k, v in analysis.__dict__.items() if k != "_sa_instance_state"}

    since  = date.today() - timedelta(days=90)
    prices = (
        db.query(DailyPrice)
        .filter(DailyPrice.ticker == analysis.ticker, DailyPrice.date >= since)
        .order_by(DailyPrice.date)
        .all()
    )
    price_history = [
        {"date": p.date.strftime("%b %d"), "close": float(p.close or 0)} for p in prices
    ]

    signal = (
        db.query(TechnicalSignal)
        .filter(TechnicalSignal.ticker == analysis.ticker)
        .order_by(TechnicalSignal.date.desc())
        .first()
    )
    technicals = {
        "ema9":          float(signal.ema9          or 0),
        "ema21":         float(signal.ema21         or 0),
        "sma50":         float(signal.sma50         or 0),
        "sma200":        float(signal.sma200        or 0),
        "adr_pct":       float(signal.adr_pct       or 0),
        "atr":           float(signal.atr           or 0),
        "atr_extension": float(signal.atr_extension or 0),
        "rvol":          float(signal.rvol          or 0),
    } if signal else {}

    raw = dict(analysis.raw_json or {})
    raw["price_history"] = price_history
    raw["technicals"]    = technicals
    row["raw_json"] = raw
    return row


@router.get("/{ticker}", response_model=AnalysisSchema)
async def get_analysis(ticker: str, db: Session = Depends(get_db)):
    t = _validate_ticker(ticker)
    result = (
        db.query(ClaudeAnalysis)
        .filter(ClaudeAnalysis.ticker == t)
        .order_by(ClaudeAnalysis.analyzed_at.desc())
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"No analysis for {t}")
    return AnalysisSchema(**_enrich(result, db))


@router.post("/{ticker}/refresh", response_model=AnalysisSchema)
async def refresh_analysis(ticker: str, db: Session = Depends(get_db)):
    t = _validate_ticker(ticker)
    result = await claude_analyzer.analyze_ticker_async(db, t)
    if not result:
        raise HTTPException(status_code=500, detail="Claude analysis failed")
    claude_analyzer._save_sync(db, t, result)
    saved = (
        db.query(ClaudeAnalysis)
        .filter(ClaudeAnalysis.ticker == ticker.upper())
        .order_by(ClaudeAnalysis.analyzed_at.desc())
        .first()
    )
    return AnalysisSchema(**_enrich(saved, db))
