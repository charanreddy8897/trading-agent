from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db_models import DailyPrice, TechnicalSignal
from app.schemas.responses import MoverSchema, MoversResponseSchema
from app.universe.sectors import ALL_TICKERS, TICKER_SECTOR

router = APIRouter()


def _get_changes(db: Session, days_back: int = 3) -> list[MoverSchema]:
    since = date.today() - timedelta(days=days_back)
    rows  = (
        db.query(DailyPrice)
        .filter(DailyPrice.ticker.in_(ALL_TICKERS), DailyPrice.date >= since)
        .order_by(DailyPrice.ticker, DailyPrice.date.desc())
        .all()
    )

    # defaultdict groups rows by ticker without a setdefault call
    by_ticker: defaultdict[str, list[DailyPrice]] = defaultdict(list)
    for r in rows:
        by_ticker[r.ticker].append(r)

    changes: list[MoverSchema] = []
    for ticker, prices in by_ticker.items():
        if len(prices) >= 2:
            cur  = float(prices[0].close)
            prev = float(prices[1].close)
            pct  = ((cur - prev) / prev) * 100 if prev else 0.0
            changes.append(MoverSchema(
                ticker=ticker,
                price=round(cur, 2),
                change_pct=round(pct, 2),
                volume=prices[0].volume,
                sector=TICKER_SECTOR.get(ticker),
            ))
    return changes


@router.get("/top", response_model=MoversResponseSchema)
async def top_movers(count: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    changes = sorted(_get_changes(db), key=lambda x: x.change_pct, reverse=True)
    return MoversResponseSchema(
        gainers=changes[:count],
        losers=list(reversed(changes[-count:])),
    )


@router.get("/unusual-volume", response_model=list[MoverSchema])
async def unusual_volume(
    threshold: float = Query(default=2.0),
    db: Session = Depends(get_db),
):
    signals = (
        db.query(TechnicalSignal)
        .filter(TechnicalSignal.rvol >= threshold)
        .order_by(TechnicalSignal.date.desc())
        .limit(20)
        .all()
    )

    results: list[MoverSchema] = []
    for sig in signals:
        latest = (
            db.query(DailyPrice)
            .filter(DailyPrice.ticker == sig.ticker)
            .order_by(DailyPrice.date.desc())
            .first()
        )
        if not latest:
            continue

        prev = (
            db.query(DailyPrice)
            .filter(DailyPrice.ticker == sig.ticker, DailyPrice.date < latest.date)
            .order_by(DailyPrice.date.desc())
            .first()
        )

        change_pct = 0.0
        if prev and prev.close:
            change_pct = ((float(latest.close) - float(prev.close)) / float(prev.close)) * 100

        results.append(MoverSchema(
            ticker=sig.ticker,
            price=float(latest.close),
            change_pct=round(change_pct, 2),
            volume=latest.volume,
            avg_volume=float(latest.volume) / float(sig.rvol) if sig.rvol else None,
            rvol=float(sig.rvol),
            sector=TICKER_SECTOR.get(sig.ticker),
        ))

    return results
