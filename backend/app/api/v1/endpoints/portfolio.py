from __future__ import annotations

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.settings import settings
from app.models.db_models import Position, PortfolioSnapshot
from app.portfolio.tracker import portfolio_tracker
from app.risk.exposure import exposure_calculator
from app.schemas.responses import (
    PerformancePoint,
    PortfolioSummarySchema,
    PositionSchema,
    RobinhoodSyncPayload,
    RobinhoodSyncResponse,
    SectorAllocationSchema,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/summary", response_model=PortfolioSummarySchema)
async def portfolio_summary(db: Session = Depends(get_db)):
    positions   = db.query(Position).all()
    total_value = sum(float(p.market_value or 0) for p in positions)
    total_pnl   = sum(float(p.unrealized_pnl or 0) for p in positions)

    latest_snap = (
        db.query(PortfolioSnapshot).order_by(PortfolioSnapshot.snapshot_at.desc()).first()
    )
    daily_change = float(latest_snap.daily_change or 0) if latest_snap else 0.0
    daily_pct    = float(latest_snap.daily_pct    or 0) if latest_snap else 0.0
    cash         = float(latest_snap.cash         or 0) if latest_snap else 0.0

    return PortfolioSummarySchema(
        total_value=round(total_value, 2),
        total_pnl=round(total_pnl, 2),
        daily_change=round(daily_change, 2),
        daily_pct=round(daily_pct, 4),
        position_count=len(positions),
        cash=round(cash, 2),
    )


@router.get("/holdings", response_model=list[PositionSchema])
async def portfolio_holdings(db: Session = Depends(get_db)):
    positions = db.query(Position).order_by(Position.market_value.desc()).all()
    return [PositionSchema.model_validate(p) for p in positions]


@router.get("/performance", response_model=list[PerformancePoint])
async def portfolio_performance(
    period: str = Query(default="1M"),
    db: Session = Depends(get_db),
):
    days_map = {"1W": 7, "1M": 30, "3M": 90, "6M": 180, "1Y": 365, "YTD": 365}
    days  = days_map.get(period, 30)
    since = date.today() - timedelta(days=days)
    snaps = (
        db.query(PortfolioSnapshot)
        .filter(PortfolioSnapshot.snapshot_at >= since)
        .order_by(PortfolioSnapshot.snapshot_at)
        .all()
    )
    return [
        PerformancePoint(date=s.snapshot_at.strftime("%b %d"), value=float(s.total_value or 0))
        for s in snaps
    ]


@router.get("/sector-allocation", response_model=SectorAllocationSchema)
async def sector_allocation(db: Session = Depends(get_db)):
    report = exposure_calculator.calc_exposure(db)
    return SectorAllocationSchema(
        sector_pcts=report.sector_pcts,
        correlated=report.correlated,
        warnings=report.warnings,
    )


@router.post("/robinhood-sync", response_model=RobinhoodSyncResponse)
async def robinhood_sync(
    payload: RobinhoodSyncPayload,
    x_sync_key: str = Header(..., alias="X-Sync-Key"),
    db: Session = Depends(get_db),
):
    """
    Receives Robinhood portfolio data posted by a local Claude Code session
    that has the Robinhood MCP authenticated.

    Protected by a static sync key (ROBINHOOD_SYNC_KEY in .env) so only
    your local machine can write to it. Not meant to be a public endpoint.
    """
    if x_sync_key != settings.robinhood_sync_key:
        raise HTTPException(status_code=401, detail="Invalid sync key")

    for pos in payload.positions:
        portfolio_tracker.upsert_position(
            db=db,
            ticker=pos.ticker,
            shares=pos.shares,
            avg_cost=pos.avg_cost,
            current_price=pos.current_price,
            entry_date=pos.entry_date,
            stop_loss=pos.stop_loss,
        )

    pf = payload.portfolio
    prev_snap = db.query(PortfolioSnapshot).order_by(PortfolioSnapshot.snapshot_at.desc()).first()
    prev_value = float(prev_snap.total_value or 0) if prev_snap else pf.total_value
    daily_change = pf.total_value - prev_value

    portfolio_tracker.snapshot_portfolio(
        db=db,
        total_value=pf.total_value,
        cash=pf.cash,
        daily_change=daily_change,
        daily_pct=pf.daily_pct,
    )

    logger.info(
        "Robinhood sync: %d positions, portfolio $%.2f",
        len(payload.positions), pf.total_value,
    )

    return RobinhoodSyncResponse(
        synced_positions=len(payload.positions),
        total_value=pf.total_value,
        status="ok",
    )
