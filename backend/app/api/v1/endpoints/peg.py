from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db_models import DailyPrice, PegSetup
from app.schemas.responses import PegSetupSchema
from app.universe.sectors import TICKER_SECTOR

router = APIRouter()


def _enrich_peg(peg: PegSetup, db: Session) -> dict:
    row = {k: v for k, v in peg.__dict__.items() if k != "_sa_instance_state"}
    row["sector"] = TICKER_SECTOR.get(peg.ticker)

    latest = (
        db.query(DailyPrice)
        .filter(DailyPrice.ticker == peg.ticker)
        .order_by(DailyPrice.date.desc())
        .first()
    )
    row["current_price"] = float(latest.close) if latest else None

    if latest and peg.peg_low:
        ema9_approx     = float(latest.close) * 0.97
        row["entry_zone"] = f"${ema9_approx:.2f} – ${float(peg.peg_low) * 1.05:.2f}"
    else:
        row["entry_zone"] = None

    return row


@router.get("/active", response_model=list[PegSetupSchema])
async def active_pegs(db: Session = Depends(get_db)):
    pegs = (
        db.query(PegSetup)
        .filter(PegSetup.gap_filled == False)  # noqa: E712
        .order_by(PegSetup.peg_date.desc())
        .all()
    )
    return [PegSetupSchema(**_enrich_peg(p, db)) for p in pegs]


@router.get("/history", response_model=list[PegSetupSchema])
async def peg_history(
    limit:  int = Query(default=50, ge=1, le=500, description="Max 500"),
    offset: int = Query(default=0,  ge=0),
    db: Session = Depends(get_db),
):
    pegs = (
        db.query(PegSetup)
        .order_by(PegSetup.peg_date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [PegSetupSchema(**_enrich_peg(p, db)) for p in pegs]
